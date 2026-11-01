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
| `herdr-app`                                                     | Desktop layouts, keys, appearance and mods; reads `herdr-app --skill` from the installed binary. |
| `herdr-core`                                                    | Persistent terminals and program operations; reads the installed `hc --skill`. |
| `herdr-cli`                                                     | The legacy TUI and its configuration; reads the installed `herdr --skill`. |
| `predictive-history`                                             | Create or update Predictive History lecture pages in Notion, with layered notes, verified sources, and native embeds. |
| `notion-to-obsidian`                                             | Export a Notion page or bounded hub into Obsidian, preserving local edits and rendering media once. |
| `notion-analyze-and-link`                                        | Review an existing Notion collection and add meaningful connections or requested synthesis. |
| `obsidian-analyze-and-link`                                      | Review existing local notes and add connections and sparse inline concept wikilinks. |
| `civilization-lecture`                                          | Compatibility entrypoint and helper paths for existing Civilization libraries. |
| `source-to-notion`                                              | Read one source deeply, explain its ideas from first principles, assess reasoning/evidence, and publish in Notion or return a private collection draft. |
| `source-collection-to-notion`                                   | Coordinate a bounded collection using the same source analyzer, with optional parallel drafts, cross-source review, shared views/guides, and verified publication. |
| `spotify-podcast-to-notion`                                     | Compatibility entrypoint for Spotify episodes; uses the shared `source-to-notion` workflow and library. |

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

The three Herdr skills are thin entrypoints, with separate names for the desktop
window, core terminals and legacy TUI. They read the relevant binary's guide each
time instead of storing a manual or API snapshot in this repository. Herdr app
also generates its customization guide and types locally. Updating Herdr therefore
updates the operational instructions without needing a matching commit here.
The normal installer links these wrappers into both agents' skill directories;
[Codex follows symlinked skill folders](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills).

Invoke `socratic-social-science` with `$socratic-social-science` in Codex or
`/socratic-social-science` in Claude Code. It replaces `socratic-learning` and
runs only when explicitly requested. Re-run the installer after this rename to
create the new links and remove the obsolete ones.

Use `$source-to-notion` in Codex or `/source-to-notion` in Claude Code with a
podcast, video, or reading link/file, including YouTube videos, Spotify episodes,
and Substack posts. It adapts acquisition to the material while retaining an
executive summary, first-principles explanation, relevant philosophical context,
argument reconstruction, cruxes, and serious objections or limitations. Its scripts handle
HTML extraction and complete Notion exports; interactive inspection and native
appearance settings use the in-app browser first, with a tested `ntn` CLI path
for supported structured work. The private default Research Library destination
stays in `~/.config/source-to-notion/destination.json` (or under `XDG_CONFIG_HOME`).
An explicitly supplied destination takes precedence.

For example: `$source-to-notion <source URL> — explain the core ideas and
philosophical context, and save the analysis in <Notion destination URL>`.
The source and destination can also be supplied in ordinary conversation.

Use `$source-collection-to-notion` or `/source-collection-to-notion` for a bounded
collection or coordinated batch. It owns inventory, dependencies, shared schema,
guides, navigation, cross-source review, and publication. When useful, separate
agents use the same `source-to-notion` skill in draft-only mode for disjoint
sources; one coordinator manages shared mutations and any read-all-before-publish
barrier. A batch does not automatically create a new database. Private snapshots,
drafts, and destination records remain outside this repository.

The former `close-reading-to-notion` analytical workflow is now part of
`source-to-notion`; use that canonical entrypoint. The older
`spotify-podcast-to-notion` entrypoint still forwards episode requests to it.
`predictive-history` retains its course-specific acquisition and teaching
conventions, and `notion-analyze-and-link` handles a later review of existing notes.

The skills are written for my own setup. They refer to each other and to my agent guides, which live in a private repo, by absolute path, because agents load them through symlinks.

## Adding one

Create `<name>/SKILL.md` in this folder, then run `./install.sh`. For a skill that should run only when invoked, set `disable-model-invocation: true` for Claude and add `agents/openai.yaml` with `policy: allow_implicit_invocation: false` for Codex. Codex doesn't substitute `$ARGUMENTS`, so say where to find the arguments when it's left as is.

A plugin whose code runs inside Claude Code, such as `/prs`, is a mod and goes in [`../mods/`](../mods/README.md).
