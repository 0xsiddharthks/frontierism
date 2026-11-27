# Crypto privacy research

Notes and runnable experiments on privacy in Bitcoin, smart contract platforms, and DeFi. For each system, track what the public can see, what counterparties or operators can learn, and what the verifier actually checks. Record deployment status alongside the design when it matters.

## Research directories

| Directory | Contents |
| --- | --- |
| [Bitcoin transaction privacy](bitcoin-privacy/README.md) | CoinJoin and BIP 78 PayJoin, with a Rust lab for UTXO accounting, PSBTs, and signature commitments. |

## Reading roadmap

Start with Bitcoin's public UTXO graph and custodial mixing, then work through CoinJoin and PayJoin. Follow-ups include WabiSabi's variable-amount CoinJoins, asynchronous PayJoin in BIP 77, and receiver privacy via Silent Payments. [CoinJoin proposal](https://bitcointalk.org/?topic=279249) · [BIP 78](https://bips.dev/78/) · [BIP 77](https://bips.dev/77/) · [BIP 352](https://bips.dev/352/)

Paul Klay's November 26, 2026 ecosystem map supplies eight tracks and 42 project examples. The project names are reading leads. Each track has a question to take to the protocol documentation. [Crypto Privacy Ecosystem Map 2026](https://x.com/PaulKlayVC/status/2126084745516003384)

| Track | Questions for the deep dive | Projects from the map |
| --- | --- | --- |
| Shielded transfers and recipient privacy | What do a deposit commitment and a nullifier prove? Who determines the approved set in Privacy Pools? What does a stealth address conceal when amounts stay public? | Tornado Cash, RAILGUN, Privacy Pools, Hinkal, Privacy Cash, Umbra, Fluidkey |
| Protocol-level payment privacy | Which details are shielded by the protocol? When can a wallet choose a transparent transaction? How do ring signatures, shielded notes, and viewing keys differ? | Monero, Zcash, Namada, Beldex |
| Programmable privacy | Where does a private function execute? Who holds its inputs and state? How does it compose with public contracts? | Aztec, Aleo, Miden, Penumbra, Midnight, Oasis |
| Confidential computing | How do fully homomorphic encryption (FHE), secure multiparty computation (MPC), and trusted execution environments (TEEs) differ in who can see the data and what a verifier trusts? | Zama, Fhenix, Inco, Arcium, Nillion, Phala, iExec |
| Private trading and MEV | Who sees an order before execution? Compare private matching, batch auctions, encrypted mempools, and private order flow. | Renegade, CoW Swap, Shutter, Flashbots |
| Identity and selective disclosure | Can a verifier check a claim such as age or residency while learning only that claim? Can it link repeated proofs? | Self, ZKPassport, Rarimo, zkPass |
| Network and metadata privacy | What can peers, relays, and network observers infer from IP addresses, timing, and message patterns? | Nym, HOPR, Session, Logos |
| Institutional privacy | Who can view amounts or state? How are audit access, issuer controls, and selective disclosure enforced? | Canton, Rayls, COTI, Partisia, TACEO, Seismic |

After Bitcoin, start with **Tornado Cash → Privacy Pools**. Read the basic deposit and withdrawal proof first, then add an association set and ask what the extra proof guarantees. Compare that model with Zcash, which supports both transparent and shielded transfers, and with recipient-link privacy in the stealth address standard. [Tornado Cash protocol](https://github.com/tornadocash/tornado-core#tornado-cash-privacy-solution) · [Privacy Pools paper](https://v1.privacypools.com/whitepaper.pdf) · [Zcash transfer types](https://z.cash/learn/what-is-the-difference-between-shielded-and-transparent-zcash/) · [ERC-5564](https://eips.ethereum.org/EIPS/eip-5564)

The Sui readings span two tracks. **zkLogin** uses an OpenID Connect credential to authorize a Sui transaction while keeping the credential private from the chain. **Confidential Transfers** uses encrypted amounts and balances with visible counterparties and issuer-designated audit access. Compare their disclosure boundaries with those of private identity and institutional payment systems. [zkLogin technical reference](https://docs.sui.io/sui-stack/zklogin-integration/zklogin) · [Confidential Transfers implementation](https://github.com/MystenLabs/confidential-transfers)
