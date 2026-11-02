use clap::Parser;
use clap::Subcommand;
use serde::Deserialize;
use std::path::Path;
use std::path::PathBuf;

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

    fn start(&self) {
        println!("Starting {}", self.config.node_name);
    }
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
    let node: Node = Node::new(config);
    node.start();

    tokio::signal::ctrl_c().await?;
    println!("Shutting down");

    Ok(())
}
