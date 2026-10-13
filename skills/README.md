# Skills

My agent skills for Claude Code and Codex.

| Skill                                                            | What it does                                                                                       |
| ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `learn`                                                          | `/learn`: saves lessons from a session into my agent guides, after I approve each change.          |
| `audit-memory`                                                   | `/audit-memory`: re-checks those guides against current code, fills gaps, and reports what it saw. |
| `pr-self-review`, `pr-groom`, `pr-address-feedback`, `pr-rebase` | For my own PRs. They chain, and share `pr-common.md`.                                              |
| `pr-peer-review`                                                 | For colleagues' PRs: keeps only real issues, and posts the review when I say so.                   |
| `socratic-social-science`                                        | Explicitly invoked Socratic tutoring for politics, economics, and social science; excludes technical instruction. |
| `xurl`                                                           | Read-only X research: linked browser for posts and threads; xurl when API access fits better.      |
| `predictive-history`                                             | Create or update Predictive History lecture pages in Notion, with layered notes, verified sources, and native embeds. |
| `notion-to-obsidian`                                             | Export a Notion page or bounded hub into Obsidian, preserving local edits and rendering media once. |
| `notion-analyze-and-link`                                        | Review an existing Notion collection and add meaningful connections or requested synthesis. |
| `obsidian-analyze-and-link`                                      | Review existing local notes and add connections and sparse inline concept wikilinks. |
| `civilization-lecture`                                          | Compatibility entrypoint and helper paths for existing Civilization libraries. |
| `spotify-podcast-to-notion`                                     | Analyze a Spotify episode in a searchable Notion library, with chapters, arguments, source checks, metadata, and tags. |

## Install

Run `install.sh` from the repo root:

```sh
./install.sh          # link every skill into ~/.claude/skills and ~/.agents/skills
./install.sh --check  # only report
```

Re-run it after adding a skill or moving this repo. `~/.agents/skills` is Codex's user skills directory.

Notion is the maintained source for the study libraries. Use `predictive-history`
to publish the requested lecture or course there; run `notion-analyze-and-link`
when a later analysis pass is wanted. Use `notion-to-obsidian` only for an explicit
local copy, and `obsidian-analyze-and-link` for a local analysis task. The latter
three skills work with other note collections too. They compose when requested;
none automatically exports, synchronizes, or launches the next skill. Invoke a
skill as `$skill-name` in Codex or `/skill-name` in Claude Code.

Invoke `socratic-social-science` with `$socratic-social-science` in Codex or
`/socratic-social-science` in Claude Code. It replaces `socratic-learning` and
runs only when explicitly requested. Re-run the installer after this rename to
create the new links and remove the obsolete ones.

Use `$spotify-podcast-to-notion` in Codex or `/spotify-podcast-to-notion` in
Claude Code with an episode link. Its private Notion destination is stored in
`~/.config/spotify-podcast-to-notion/destination.json` (or under `XDG_CONFIG_HOME`),
outside this public repository.

The skills are written for my own setup. They refer to each other and to my agent guides, which live in a private repo, by absolute path, because agents load them through symlinks.

## Adding one

Create `<name>/SKILL.md` in this folder, then run `./install.sh`. For a skill that should run only when invoked, set `disable-model-invocation: true` for Claude and add `agents/openai.yaml` with `policy: allow_implicit_invocation: false` for Codex. Codex doesn't substitute `$ARGUMENTS`, so say where to find the arguments when it's left as is.

A plugin whose code runs inside Claude Code, such as `/prs`, is a mod and goes in [`../mods/`](../mods/README.md).
