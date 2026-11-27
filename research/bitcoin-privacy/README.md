# CoinJoin and BIP 78 PayJoin

Bitcoin verifies that each input is authorized to spend an earlier output. A transaction can collect those authorizations from different owners. The usual assumption that every input belongs to one wallet works often enough to be useful for analytics, but it can merge unrelated wallets into one cluster. CoinJoin and PayJoin both exploit the gap between what consensus verifies and what an observer infers. [Bitcoin transaction guide](https://developer.bitcoin.org/devguide/transactions.html) · [Original CoinJoin proposal](https://bitcointalk.org/?topic=279249)

## CoinJoin and equal outputs

In a simple equal-output CoinJoin, each participant supplies an input and specifies a destination for one output of the same value as everyone else's. A transaction proposal brings those inputs and outputs together. Each participant checks their expected output and the fee and change they agreed to, then supplies the signature for their input. Bitcoin accepts the transaction once every input is properly authorized and it satisfies the other consensus rules. A coordinator can arrange the round without taking custody of the inputs. [Original CoinJoin proposal](https://bitcointalk.org/?topic=279249)

The Rust fixture spends inputs of **80,000**, **85,000**, and **94,000 sat**. It creates three outputs of **50,000 sat** to different scripts of the same type, plus **29,700**, **34,700**, and **43,700 sat** of change. The fee is **900 sat**. Every amount is visible. An observer who knows one of the original inputs has three equal-sized candidates for that participant's output from the transaction alone, under the assumption of one equal output per participant.

The size of that candidate set is a starting point. A coordinator that collects the input and output together can know the mapping. Other observers might infer change ownership, recognize the transaction format, or observe later spending that links an output back to a known input owner. WabiSabi uses anonymous credentials so a coordinator can verify how much value a participant may register while the protocol hides the link between their input and output registrations. This accommodates variable amounts, with the amount pattern and other public data still available to an observer. [WabiSabi paper](https://cryptoeconomicsystems.pubpub.org/pub/ficsor-wabisabi-coordinated/release/3) · [Study of CoinJoin privacy](https://arxiv.org/abs/2109.10229)

## PayJoin uses the payment itself

Alice owes a merchant **40,000 sat**. In an ordinary payment, Alice supplies every input. With PayJoin, the merchant brings an input too. The merchant gets a larger output because it merges the payment with the value the merchant already owned, minus any extra fee the merchant covers. Alice pays the same total. The final transaction can have the familiar shape of a multi-input payment with change. [BIP 78 motivation](https://github.com/bitcoin/bips/blob/master/bip-0078.mediawiki#motivation)

| Amount | Ordinary payment | PayJoin |
| --- | ---: | ---: |
| Alice's input | 100,000 sat | 100,000 sat |
| Merchant's input | — | 20,000 sat |
| Payment output to merchant | 40,000 sat | 59,800 sat |
| Change output to Alice | 59,500 sat | 59,500 sat |
| Network fee | 500 sat | 700 sat |
| Alice's net spend | 40,500 sat | 40,500 sat |
| Merchant's net gain | 40,000 sat | 39,800 sat |

The two inputs belong to different parties. The 59,800 sat output includes funds the merchant already held, and the merchant's net gain accounts for the extra 200 sat fee. An observer sees the final inputs and outputs. The parties involved in the negotiation see the payment and the proposal, and an observer with the invoice or other wallet data can draw stronger inferences. Wider use can make common-input clustering less reliable even for payments that involve a single wallet. [BIP 78 rationale](https://github.com/bitcoin/bips/blob/master/bip-0078.mediawiki#impacted-heuristics)

### How BIP 78 negotiates the transaction

1. **Invoice.** The receiver presents a Bitcoin payment URI with a `pj` endpoint. The URI can carry `pjos=0` to require the sender to disable payment-output substitution. [BIP 78 payment parameters](https://github.com/bitcoin/bips/blob/master/bip-0078.mediawiki#bip21-payjoin-parameters)
2. **Original PSBT.** The sender creates a standard transaction that pays the invoice, signs and finalizes it, and sends it to the receiver as a base64-encoded Partially Signed Bitcoin Transaction (PSBT). The format carries the transaction alongside signing data, such as prevouts and signatures, and can also hold a fully signed transaction. The original is already broadcastable as an ordinary payment if negotiation fails. [BIP 78 protocol](https://github.com/bitcoin/bips/blob/master/bip-0078.mediawiki#protocol) · [BIP 174 PSBT format](https://bips.dev/174/)
3. **Proposal.** The receiver checks the original, adds its own input in this example, and increases its payment output. Existing inputs and outputs keep their relative order, and new entries can be inserted between them. The proposal carries prevout data and final signatures for the receiver's added inputs. The sender matches its own inputs by outpoint and restores their prevout data locally. [BIP 78 proposal requirements](https://github.com/bitcoin/bips/blob/master/bip-0078.mediawiki#protocol)
4. **Verify, sign, broadcast.** The sender checks the proposal against the original before re-signing its own inputs. It checks the original outpoints and their sequence numbers, version and lock time, outputs and allowed substitutions, and fees. If the sender authorizes an extra fee contribution, it identifies an output and caps the amount. The receiver pays the extra fee in the lab. Successful negotiation produces one transaction for broadcast. [BIP 78 sender checklist](https://github.com/bitcoin/bips/blob/master/bip-0078.mediawiki#senders-payjoin-proposal-checklist) · [Fee rules](https://github.com/bitcoin/bips/blob/master/bip-0078.mediawiki#fee-output)

Adding an input raises transaction weight. BIP 78 requires the proposal's absolute fee to be at least the original fee. The sender can also request a minimum rate in satoshis per virtual byte and check it after signing. Any authorized sender contribution is limited to fees for the added inputs. [BIP 78 fee rules](https://github.com/bitcoin/bips/blob/master/bip-0078.mediawiki#fee-output) · [Sender checklist](https://github.com/bitcoin/bips/blob/master/bip-0078.mediawiki#senders-payjoin-proposal-checklist)

**Why sign twice?** With SegWit v0 `SIGHASH_ALL`, the signature digest commits to the transaction's input outpoints and outputs, among other fields. The merchant's input and the changed payment output alter Alice's digest. Her signature for the original commits to the ordinary payment. The new signature authorizes the proposal. Both versions spend the same Alice UTXO, so only one can settle on-chain. BIP 77 changes the transport by using an asynchronous directory and encrypted messages. [BIP 143](https://bips.dev/143/) · [BIP 77](https://bips.dev/77/)

## Run the Rust lab

From the repository root, with Rust 1.85 or newer:

```sh
cargo run --locked --manifest-path research/bitcoin-privacy/Cargo.toml
cargo test --locked --manifest-path research/bitcoin-privacy/Cargo.toml
```

The [lab](src/main.rs) uses `rust-bitcoin` and synthetic prevouts. It works at the unsigned transaction layer and carries the prevout metadata in real BIP 174 PSBTs. It round-trips the proposal through PSBT encoding, restores the sender's prevout by matching its outpoint, and uses both prevouts to compute the fee. It prints the CoinJoin and both payment shapes, then computes the sender's BIP 143 digest before and after. A test verifies that the fixture check rejects reduced sender change. The lab runs locally and models the transaction edits and a subset of sender checks. The BIP's wire exchange, signing, fallback, and relay-policy rules belong to the full specification. [rust-bitcoin](https://github.com/rust-bitcoin/rust-bitcoin) · [BIP 78](https://bips.dev/78/)
