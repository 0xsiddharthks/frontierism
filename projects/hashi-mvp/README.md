# Hashi MVP

A small Rust node for learning Rust alongside the public
[Hashi codebase](https://github.com/MystenLabs/hashi). The project and its learning
record live in `frontierism/projects/hashi-mvp`.

## Resume in a new chat

Give any assistant this prompt, with access to this folder:

> Continue my Rust and Hashi learning in `projects/hashi-mvp`. Read this folder's
> `AGENTS.md`, `learning-context.md`, `progress.md`, and `src/main.rs`. Briefly
> explain where we stopped, then follow the next-session plan in `progress.md`.
> Teach directly at a reasonable pace, using my TypeScript, C++ and Solidity
> background. Keep the progress record current as we work.

For a chat without repository access, attach those four files, `Cargo.toml` and
`node.toml`.

- [Learning context](learning-context.md): original request and teaching preferences.
- [Progress](progress.md): implemented features, concepts covered, gaps and next steps.
- [Agent instructions](AGENTS.md): how to continue and maintain the handoff.

## Run the current milestone

From this directory:

```sh
cargo check --locked -p hashi-mvp
cargo run --locked -p hashi-mvp -- server --config node.toml
```

In another terminal, with the supplied configuration:

```sh
curl http://127.0.0.1:3000/health
curl http://127.0.0.1:3000/info
```

The responses are `ok` followed by a newline, and `{"node_name":"node-0"}`.
Press Ctrl+C in the server terminal to shut down.

From the `frontierism` root, use
`cargo run --locked -p hashi-mvp -- server --config projects/hashi-mvp/node.toml`.
