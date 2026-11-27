use bitcoin::absolute::LockTime;
use bitcoin::hashes::Hash;
use bitcoin::psbt::Psbt;
use bitcoin::sighash::{EcdsaSighashType, SegwitV0Sighash, SighashCache};
use bitcoin::transaction::Version;
use bitcoin::{Amount, OutPoint, ScriptBuf, Sequence, Transaction, TxIn, TxOut, Txid, WPubkeyHash};

struct FixtureUtxo {
    outpoint: OutPoint,
    output: TxOut,
}

impl FixtureUtxo {
    fn new(marker: u8, sats: u64) -> Self {
        Self {
            outpoint: OutPoint::new(Txid::from_byte_array([marker; 32]), 0),
            output: p2wpkh_output(marker, sats),
        }
    }

    fn spend(&self) -> TxIn {
        TxIn {
            previous_output: self.outpoint,
            sequence: Sequence::ENABLE_RBF_NO_LOCKTIME,
            ..TxIn::default()
        }
    }
}

fn p2wpkh_output(marker: u8, sats: u64) -> TxOut {
    TxOut {
        value: Amount::from_sat(sats),
        script_pubkey: ScriptBuf::new_p2wpkh(&WPubkeyHash::from_byte_array([marker; 20])),
    }
}

fn fixture_psbt(inputs: &[&FixtureUtxo], outputs: Vec<TxOut>) -> Psbt {
    let transaction = Transaction {
        version: Version::TWO,
        lock_time: LockTime::ZERO,
        input: inputs.iter().map(|utxo| utxo.spend()).collect(),
        output: outputs,
    };
    let mut psbt = Psbt::from_unsigned_tx(transaction).expect("valid unsigned fixture");
    for (input, utxo) in psbt.inputs.iter_mut().zip(inputs) {
        input.witness_utxo = Some(utxo.output.clone());
    }
    psbt
}

fn show_transaction(label: &str, psbt: &Psbt) -> u64 {
    // Input values come from the prevouts, which the PSBT carries alongside the transaction.
    let inputs: Vec<_> = psbt
        .iter_funding_utxos()
        .map(|utxo| utxo.expect("fixture has each prevout").value.to_sat())
        .collect();
    let outputs: Vec<_> = psbt
        .unsigned_tx
        .output
        .iter()
        .map(|output| output.value.to_sat())
        .collect();
    let fee = psbt.fee().expect("fixture has a valid fee").to_sat();

    println!("{label}");
    println!("  Inputs  {inputs:?} sat");
    println!("  Outputs {outputs:?} sat");
    println!("  Fee     {fee} sat");
    fee
}

fn coinjoin_demo() {
    let alice = FixtureUtxo::new(1, 80_000);
    let bob = FixtureUtxo::new(2, 85_000);
    let carol = FixtureUtxo::new(3, 94_000);
    let inputs = [&alice, &bob, &carol];
    let joint = fixture_psbt(
        &inputs,
        vec![
            p2wpkh_output(11, 50_000),
            p2wpkh_output(12, 50_000),
            p2wpkh_output(13, 50_000),
            p2wpkh_output(14, 29_700),
            p2wpkh_output(15, 34_700),
            p2wpkh_output(16, 43_700),
        ],
    );
    assert_eq!(show_transaction("Equal-output CoinJoin", &joint), 900);
}

fn payjoin_fixture() -> (Psbt, Psbt) {
    let sender = FixtureUtxo::new(21, 100_000);
    let receiver = FixtureUtxo::new(22, 20_000);
    let original = fixture_psbt(
        &[&sender],
        vec![p2wpkh_output(23, 40_000), p2wpkh_output(24, 59_500)],
    );
    let mut proposal_tx = original.unsigned_tx.clone();
    // Pick a fixed insertion point for this example. Alice's input moves to index 1.
    proposal_tx.input.insert(0, receiver.spend());
    proposal_tx.output[0].value += receiver.output.value - Amount::from_sat(200);

    // As in BIP 78, the proposal carries prevout data only for the added input.
    let mut proposal = Psbt::from_unsigned_tx(proposal_tx).expect("valid unsigned fixture");
    proposal.inputs[0].witness_utxo = Some(receiver.output);

    (original, proposal)
}

// The fixture keeps both output scripts and the sender's change amount fixed.
fn check_fixture_terms(original: &Psbt, proposal: &Psbt) -> Result<(), &'static str> {
    let original = &original.unsigned_tx;
    let proposed = &proposal.unsigned_tx;
    if original.version != proposed.version || original.lock_time != proposed.lock_time {
        return Err("transaction version or lock time changed");
    }
    let [first, second] = proposed.input.as_slice() else {
        return Err("expected exactly two inputs");
    };
    if !proposed.input.contains(&original.input[0])
        || first.previous_output == second.previous_output
    {
        return Err("expected the original input and one distinct input");
    }
    let [payment, change] = proposed.output.as_slice() else {
        return Err("expected exactly two outputs");
    };
    if *change != original.output[1] {
        return Err("sender change differs from the original");
    }
    let original_payment = &original.output[0];
    if payment.script_pubkey != original_payment.script_pubkey
        || payment.value < original_payment.value
    {
        return Err("payment script changed or amount decreased");
    }
    Ok(())
}

fn sender_digest(psbt: &Psbt, index: usize) -> SegwitV0Sighash {
    let prevout = psbt.inputs[index]
        .witness_utxo
        .as_ref()
        .expect("sender prevout data is available");
    SighashCache::new(&psbt.unsigned_tx)
        .p2wpkh_signature_hash(
            index,
            &prevout.script_pubkey,
            prevout.value,
            EcdsaSighashType::All,
        )
        .expect("fixture prevout is P2WPKH")
}

fn payjoin_demo() {
    let (original, proposal) = payjoin_fixture();
    let mut proposal = Psbt::deserialize(&proposal.serialize()).expect("proposal PSBT round-trip");
    check_fixture_terms(&original, &proposal).expect("proposal preserves the fixture's terms");

    let sender_outpoint = original.unsigned_tx.input[0].previous_output;
    let sender_index = proposal
        .unsigned_tx
        .input
        .iter()
        .position(|input| input.previous_output == sender_outpoint)
        .expect("sender input is present");
    // Restore the sender prevout locally using its outpoint because its index changed.
    proposal.inputs[sender_index]
        .witness_utxo
        .clone_from(&original.inputs[0].witness_utxo);

    let original_fee = show_transaction("Ordinary payment", &original);
    let proposal_fee = show_transaction("PayJoin proposal", &proposal);
    assert_eq!(original_fee, 500);
    assert_eq!(proposal_fee, 700);

    let original_digest = sender_digest(&original, 0);
    let proposal_digest = sender_digest(&proposal, sender_index);
    assert_ne!(original_digest, proposal_digest);
    println!("  Sender's SIGHASH_ALL digest for the original  {original_digest}");
    println!("  Sender's SIGHASH_ALL digest for the proposal  {proposal_digest}");
}

fn main() {
    coinjoin_demo();
    println!();
    payjoin_demo();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_receiver_input_added_before_sender_input() {
        let (original, proposal) = payjoin_fixture();
        assert_eq!(check_fixture_terms(&original, &proposal), Ok(()));
    }

    #[test]
    fn rejects_reduced_sender_change() {
        let (original, mut proposal) = payjoin_fixture();
        proposal.unsigned_tx.output[1].value -= Amount::from_sat(1);
        assert_eq!(
            check_fixture_terms(&original, &proposal),
            Err("sender change differs from the original")
        );
    }
}
