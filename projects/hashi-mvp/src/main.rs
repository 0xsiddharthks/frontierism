struct Config {
    node_name: String,
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

fn main() {
    let config: Config = Config {
        node_name: String::from("node-0"),
    };
    let node: Node = Node::new(config);
    node.start();
}
