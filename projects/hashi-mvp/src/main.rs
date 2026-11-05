use axum::Json;
use axum::Router;
use axum::extract::State;
use axum::routing::get;
use clap::Parser;
use clap::Subcommand;
use serde::Deserialize;
use serde::Serialize;
use std::net::SocketAddr;
use std::path::Path;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::net::TcpListener;

#[derive(Parser)]
struct Args {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Server {
        #[arg(long)]
        config: PathBuf,
    },
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Config {
    node_name: String,
    listen_addr: SocketAddr,
}

impl Config {
    fn load(path: &Path) -> anyhow::Result<Self> {
        let text: String = std::fs::read_to_string(path)?;

        let config: Config = toml::from_str(&text)?;

        anyhow::ensure!(
            !config.node_name.trim().is_empty(),
            "node_name must not be empty"
        );

        Ok(config)
    }
}

struct Node {
    config: Config,
}

impl Node {
    fn new(config: Config) -> Self {
        Node { config }
    }

    async fn start(self: Arc<Self>) -> anyhow::Result<()> {
        let app = Router::new()
            .route("/health", get(health))
            .route("/info", get(info))
            .with_state(Arc::clone(&self));

        let listener = TcpListener::bind(self.config.listen_addr).await?;

        println!(
            "{} listening on http://{}",
            self.config.node_name,
            listener.local_addr()?
        );

        axum::serve(listener, app)
            .with_graceful_shutdown(shutdown_signal())
            .await?;

        Ok(())
    }
}

#[derive(Serialize)]
struct NodeInfo {
    node_name: String,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let args = Args::parse();

    match args.command {
        Commands::Server { config } => run_server(config).await,
    }
}

async fn run_server(config_path: PathBuf) -> anyhow::Result<()> {
    let config: Config = Config::load(&config_path)?;
    let node = Arc::new(Node::new(config));
    node.start().await
}

async fn health() -> &'static str {
    "ok\n"
}

async fn info(State(node): State<Arc<Node>>) -> Json<NodeInfo> {
    Json(NodeInfo {
        node_name: node.config.node_name.clone(),
    })
}

async fn shutdown_signal() {
    tokio::signal::ctrl_c()
        .await
        .expect("failed to listen for Ctrl+C");

    println!("Shutting down");
}
