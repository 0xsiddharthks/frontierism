use serde::Deserialize;
use std::path::Path;

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

fn main() -> anyhow::Result<()> {
    let config: Config = Config::load(Path::new("node.toml"))?;
    let node: Node = Node::new(config);
    node.start();
    Ok(())
}
