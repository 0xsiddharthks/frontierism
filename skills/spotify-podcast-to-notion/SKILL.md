---
name: spotify-podcast-to-notion
description: Compatibility entrypoint for Spotify episode-to-Notion requests and the former podcast research workflow. Delegates to source-to-notion, which also supports YouTube videos and long-form readings.
---

# Spotify Podcast to Notion

Read and follow [the Source to Notion skill](../source-to-notion/SKILL.md), preserving the user's supplied episode and analysis focus. Its Spotify transcript reference contains the extraction procedure.

Honor the canonical skill's execution context: a direct episode request uses the supplied destination or shared **Research Library**; a collection worker returns a private draft without Notion writes or default-library lookup. The shared skill describes migration from legacy destination configuration. Do not create a new Podcast Research wrapper or a separate podcast-only database.
