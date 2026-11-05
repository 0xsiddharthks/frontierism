# Projects

Hands-on learning projects and experiments.

- [Hashi MVP](hashi-mvp/): A step-by-step project for learning Rust and understanding Hashi's protocol, local setup, and infrastructure.

Rust projects are members of the root Cargo workspace. From the repository root:

```sh
cargo check --workspace
cargo run -p hashi-mvp -- server --config projects/hashi-mvp/node.toml
```
