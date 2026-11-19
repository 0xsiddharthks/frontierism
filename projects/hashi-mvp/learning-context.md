# Learning context

## Goal and background

Learn Rust deeply while developing a full understanding of Hashi. The learner is
an experienced software engineer with TypeScript, C++ and Solidity experience,
but much of their Rust work has been AI-assisted. Use the small MVP to make
patterns concrete, then connect them to the public Hashi implementation.

Use a direct, reasonably paced walkthrough. Introduce Rust concepts where they
appear in real code, explain the system behavior alongside the syntax, and use
familiar-language comparisons where helpful. The Socratic learning skill is
reserved for political science and philosophy.

## Original teaching request

The teaching request below is preserved verbatim. Its separate note about the
old absolute progress-file path is summarized afterwards for portability.

> Hey Codex. I want to basically learn Rust. while I have been working on the rust codebase for quite a while, I feel like I have mostly been focussing a lot more on AI assisted coding. so I never quite needed to explicitly learn rust fully apart from just the bare minimums. So I want you to do a full walkthrough of the hashi codebase with me. and basically teach me what's going on here. and also help me read through and reason through rust and the different patterns we are using. and simultanously learn rust and also develop a full understanding of what is happening. so lets go over the hashi binary together and start understanding things?
> (btw I know there is a socratic learning skill i have installed. but do not use it. I want to use that for studying political science and philosophical concepts. not code).
> ok you remember I have tried a bunch of times now to properly understand exactly the core ideas and concepts of this repo.
> Lets start with a slightly reasonably paced guided view of everything. you take me over things step by step.
> Now, again, just to give you some context, I have been a software engineer for multiple years before this. so I am aware of concepts in Typescript and C++ and also solidity programming. I have decent credentials and should be able to jog along properly I believe.

The original request also asked for a persistent record of Rust primitives,
concepts and code locations covered. That record is now [progress.md](progress.md)
in this folder. It distinguishes introduction from demonstrated understanding.

## Source references

- Learning implementation: [src/main.rs](src/main.rs).
- Real Hashi binary: [`crates/hashi/src/main.rs`](https://github.com/MystenLabs/hashi/blob/main/crates/hashi/src/main.rs), especially `main` and `run_server`.
- Real Hashi configuration: [`crates/hashi/src/config.rs`](https://github.com/MystenLabs/hashi/blob/main/crates/hashi/src/config.rs), especially `Config::load`.
- Real Hashi node: [`crates/hashi/src/lib.rs`](https://github.com/MystenLabs/hashi/blob/main/crates/hashi/src/lib.rs), especially `Hashi::new` and `Hashi::start`.

Use a current local Hashi checkout when available. Otherwise read the public
source; the MVP is a teaching model and does not implement the bridge protocol.
