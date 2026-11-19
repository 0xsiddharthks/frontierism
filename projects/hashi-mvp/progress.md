# Rust through Hashi — progress

Updated: 2026-11-19

## Current position

The canonical project and learning record are in `frontierism/projects/hashi-mvp`.
The current MVP milestone is a configurable async HTTP node with shared state.

The last explicitly recorded walkthrough of real Hashi stopped after CLI
dispatch into `run_server`, before its body. The MVP currently includes shared
state and HTTP handlers. The implementation and teaching records describe
different kinds of progress; implemented code does not establish mastery.

## Next session

Start in the MVP's `run_server` in `src/main.rs`. Explain the existing startup
path in small steps:

1. Follow `Config::load(&config_path)`: `PathBuf` ownership, borrowing as `&Path`,
   deserializing TOML, validation, and propagating `Result` errors with `?`.
2. Follow `Arc::new(Node::new(config))` into `Node::start(self: Arc<Self>)`:
   ownership of the node, `Arc::clone`, and the shared state passed to Axum.
3. Read `info(State(node): State<Arc<Node>>) -> Json<NodeInfo>`: the extractor,
   destructuring, serialization, and why the response clones `node_name`.
4. Connect these patterns to the real Hashi `run_server`, then continue its
   logging, error context and metrics setup before `Hashi::new` and `Hashi::start`.

No next feature is recorded. If the learner demonstrates that a step is
already comfortable, record that and move forward without repeating a full lesson.

## Implemented in the MVP

These features are present in the current source, not claims about mastery.

| Feature | Source symbols |
| --- | --- |
| Clap `server --config` command and dispatch | `Args`, `Commands`, `main` |
| TOML config with `node_name` and `listen_addr` | `Config`, `Config::load` |
| Reject unknown fields and blank node names | `deny_unknown_fields`, `anyhow::ensure!` |
| Tokio runtime and asynchronous TCP listener | `main`, `Node::start` |
| Shared node configuration in Axum handlers | `Arc<Node>`, `with_state`, `State` |
| `GET /health` returns `ok\n` | `health` |
| `GET /info` returns JSON containing `node_name` | `NodeInfo`, `info` |
| Graceful shutdown on Ctrl+C | `shutdown_signal`, `with_graceful_shutdown` |

The milestone's recorded implementation sequence is: bare binary, config
loading, CLI arguments, Tokio, listener binding, then shared state. There are no
automated tests in the current MVP. Runtime behavior must be checked separately
from reading the source.

## Rust concepts

“Introduced” means explained in the recorded walkthrough. “Present in code”
means the MVP uses it, with no recorded confirmation of independent understanding.

| Concept | Status and concrete example |
| --- | --- |
| Workspace, package, binary/library crate, imports | Introduced through real Hashi's Cargo layout and `use hashi::Hashi` |
| Structs and enums carrying data | Introduced: `Args`, `Commands::Server` |
| Derive macros and attributes | Introduced: Clap parser; generated implementations deferred |
| Matching and destructuring | Introduced: `Commands::Server { config }` |
| Ownership transfer | Introduced: moving `PathBuf` into `run_server` |
| Futures, async/await and Tokio | Introduced; scheduling and polling need a deeper pass |
| `Result`, unit and expression returns | Introduced: `anyhow::Result<()>`, final `match` expression |
| Borrowing, path coercion and `?` | Present in code; resume at `Config::load` |
| `impl`, `Self`, constructors and receivers | Present in code: `Config` and `Node` |
| Serde deserialization and validation | Present in code: `Config::load` |
| `Arc` and shared ownership | Present in code: `run_server`, `Node::start` |
| Axum extractors, generics and JSON responses | Present in code: `State<Arc<Node>>`, `Json<NodeInfo>` |
| String cloning versus cloning an `Arc` | Present in code; explain their different costs and effects |
| Shutdown futures and signal handling | Present in code; not yet recorded as taught |

## Open points from earlier notes

- How `&PathBuf` becomes `&Path` at a function boundary.
- How `?` propagates an error. It returns early with an error value; it does not
  throw a C++ or JavaScript exception. `anyhow::Result<T>` aliases
  `Result<T, anyhow::Error>` with its default error type.
- Why error-context and metric APIs use closures; closure capture and `move`.
- How `.await` can suspend a task, how that differs from spawning a task, and
  why calling a Rust async function alone does not execute its body.

## Session record

### 2026-10-10 — Real Hashi entry point

Covered the workspace/package/crate structure, `Args::parse`, the
`Commands::Server` arm, destructuring and ownership transfer into `run_server`.
Introduced Tokio's entry macro, futures, `.await`, `Result<()>`, and the final
`match` expression's return value. Stopped before the body of `run_server`.
No independent exercise or understanding check was recorded.

Code visited: the root Cargo manifest, `crates/hashi/Cargo.toml`, and
`crates/hashi/src/main.rs`. Identified `crates/hashi/src/lib.rs` as the library
entry point; its internals remain ahead in the recorded walkthrough.

### 2026-11-19 — Continuation handoff

Kept the learning project in `frontierism/projects/hashi-mvp`. Captured the
original request, existing MVP milestone and next-session plan in this folder.
The earlier progress record supplied the teaching history; the current source
supplied the implemented-feature inventory. This was a documentation session,
not evidence that new Rust concepts were learned.

Validation on this date: `cargo build --locked -p hashi-mvp` passed. A local smoke
check using the sample config with an OS-assigned loopback port verified startup,
both HTTP responses and a successful Ctrl+C shutdown. Blank node names and
unknown config fields were rejected. Local documentation links and the
`CLAUDE.md` link to `AGENTS.md` were checked. The Rust source was unchanged.

## Route after startup

1. Configuration, borrowing, `Result`, error context, closures and metrics.
2. `Hashi::new`: structs, ownership, `Arc`, initialization and local storage.
3. `Hashi::start` and service lifetime: tasks, locks, channels and shutdown.
4. Sui state tracking and Bitcoin monitoring.
5. Deposits, withdrawals, peer validation and transaction execution.
6. MPC, committee reconfiguration, guardian interaction and restart recovery.
