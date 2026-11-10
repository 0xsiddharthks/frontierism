#!/bin/bash
# Claude Code statusLine — robbyrussell-style, extended.
# Reads the statusLine JSON payload on stdin and renders a one-line prompt.
# Palette follows the OS appearance (macOS "Auto" flips at sunset; Warp tracks
# it): light uses the standard ANSI colors + dim; dark uses the bright variants
# and a solid gray for labels, because standard colors and the dim attribute
# both go muddy against a dark background. Force with STATUSLINE_THEME=dark|light.
input=$(cat)

# Single jq call -> \x1f-separated fields (keeps the statusLine fast). Not tabs:
# tab is IFS whitespace, so `read` would drop empty fields and shift the rest.
vals=$(echo "$input" | jq -r '
  def ktok: if . >= 999500 then "\(. / 100000 | round / 10)M" else "\(. / 1000 | round)k" end;
  [
    (.workspace.current_dir // .cwd // "."),
    (.workspace.repo.name // ""),
    (.workspace.git_worktree // ""),
    (.model.display_name // "Claude"),
    (.context_window.context_window_size // 0),
    (.effort.level // ""),
    (.context_window.remaining_percentage // ""),
    (.prompt_cache // {}
      | if .caching_observed and (.warm == false or (.expires_at // infinite) <= now)
        then (.recache_tokens_if_cold // 0 | if . > 0 then ktok else "" end) else "" end),
    (.rate_limits.five_hour.used_percentage // "" | if . == "" then . else round end),
    (.rate_limits.five_hour.resets_at // "" | if . == "" then . else strflocaltime("%H:%M") end),
    (.rate_limits.seven_day.used_percentage // "" | if . == "" then . else round end),
    (.rate_limits.seven_day.resets_at // "" | if . == "" then . else strflocaltime("%a %H:%M") end),
    (.cost.total_lines_added // ""),
    (.cost.total_lines_removed // ""),
    (.cost.total_cost_usd // "")
  ] | join("\u001f")')
IFS=$'\x1f' read -r full_dir repo worktree model ctx_size effort remaining cold h5 h5_reset d7 d7_reset added removed cost <<<"$vals"

dir=$(basename "$full_dir")
# A linked worktree's directory name is throwaway; the repo is the useful label.
[ -n "$worktree" ] && [ -n "$repo" ] && dir="$repo"
model=${model#Claude }   # strip leading "Claude " to save width
model=${model% (*)}      # drop trailing "(… context)"; the ·1M badge covers it

# ── theme-aware palette ────────────────────────────────────────────────────
case "${STATUSLINE_THEME:-$(defaults read -g AppleInterfaceStyle 2>/dev/null)}" in
  [Dd]ark) theme=dark ;;
  *)       theme=light ;;
esac
R='\033[0m'
if [ "$theme" = dark ]; then
  c_arrow='\033[1;92m'; c_dir='\033[1;96m'; c_gitp='\033[1;94m'; c_branch='\033[0;91m'
  c_dirty='\033[1;93m'; c_ahead='\033[0;92m'; c_behind='\033[0;93m'
  c_model='\033[0;96m'; c_1m='\033[1;96m';    c_mut='\033[0;90m'
  c_add='\033[0;92m';   c_rem='\033[0;91m'
  e_low=94; e_med=96; e_high=93; e_xhigh=95; e_max=91
  x_good='0;92'; x_warn='0;93'; x_bad='0;91'
else
  c_arrow='\033[1;32m'; c_dir='\033[1;36m'; c_gitp='\033[1;34m'; c_branch='\033[0;31m'
  c_dirty='\033[1;33m'; c_ahead='\033[0;32m'; c_behind='\033[0;33m'
  c_model='\033[0;36m'; c_1m='\033[1;36m';    c_mut='\033[2m'
  c_add='\033[0;32m';   c_rem='\033[0;31m'
  e_low=34; e_med=36; e_high=33; e_xhigh=35; e_max=31
  x_good='0;32'; x_warn='0;33'; x_bad='0;31'
fi

# ── prompt arrow + current dir (·wt marks a linked worktree) ──────────────
line="${c_arrow}➜${R}  ${c_dir}${dir}${R}"
[ -n "$worktree" ] && line="${line}${c_mut}·wt${R}"

# ── git:(branch) ✗ ⇡ahead ⇣behind ─────────────────────────────────────────
# One `git status --branch --porcelain` call gives branch, dirty, ahead/behind.
# --no-optional-locks: this runs alongside the agent's own git commands, and
# status would otherwise take index.lock to refresh the index.
status=$(git -C "$full_dir" --no-optional-locks status --branch --porcelain=v1 2>/dev/null)
if [ -n "$status" ]; then
  header=$(printf '%s\n' "$status" | head -1)
  branch=$(printf '%s' "$header" | sed -E 's/^## //; s/\.\.\..*//; s/ .*//')
  case "$header" in *'(no branch)'*) branch=$(git -C "$full_dir" rev-parse --short HEAD 2>/dev/null);; esac
  line="${line}  ${c_gitp}git:(${c_branch}${branch}${c_gitp})${R}"

  # dirty = any porcelain line beyond the ## header
  [ "$(printf '%s\n' "$status" | wc -l | tr -d ' ')" -gt 1 ] && line="${line} ${c_dirty}✗${R}"

  ahead=$(printf '%s' "$header"  | grep -oE 'ahead [0-9]+'  | grep -oE '[0-9]+')
  behind=$(printf '%s' "$header" | grep -oE 'behind [0-9]+' | grep -oE '[0-9]+')
  [ -n "$ahead" ]  && line="${line} ${c_ahead}⇡${ahead}${R}"
  [ -n "$behind" ] && line="${line} ${c_behind}⇣${behind}${R}"
fi

# ── model (+ 1M badge for a 1M context window) ────────────────────────────
line="${line}  ${c_model}${model}${R}"
[ "${ctx_size:-0}" -ge 1000000 ] 2>/dev/null && line="${line}${c_1m}·1M${R}"

# ── reasoning effort (color-coded by intensity) ───────────────────────────
if [ -n "$effort" ]; then
  case "$effort" in
    low)    ec="$e_low" ;;
    medium) ec="$e_med" ;;
    high)   ec="$e_high" ;;
    xhigh)  ec="$e_xhigh" ;;
    max)    ec="$e_max" ;;
    *)      ec="$e_med" ;;
  esac
  line="${line}  ${c_mut}effort:${R}\033[1;${ec}m${effort}${R}"
fi

# ── context window remaining (color-coded by headroom) ────────────────────
if [ -n "$remaining" ]; then
  ri=$(printf "%.0f" "$remaining")
  if   [ "$ri" -ge 50 ]; then cc="$x_good"
  elif [ "$ri" -ge 20 ]; then cc="$x_warn"
  else                        cc="$x_bad"; fi
  line="${line}  ${c_mut}ctx:${R}\033[${cc}m${ri}%${R}"
fi

# ── prompt cache gone cold: tokens the next request re-caches ─────────────
[ -n "$cold" ] && line="${line}  ${c_mut}cold:${R}\033[${x_warn}m${cold}${R}"

# ── rate limits used (reset time once a window is ≥80% spent) ─────────────
limit() {
  [ -n "$2" ] || return
  if   [ "$2" -ge 80 ]; then lc="$x_bad";  reset="${c_mut}→$3${R}"
  elif [ "$2" -ge 50 ]; then lc="$x_warn"; reset=""
  else                       lc="$x_good"; reset=""; fi
  limits="${limits:+$limits }${c_mut}$1:${R}\033[${lc}m$2%${R}${reset}"
}
limits=""
limit 5h "$h5" "$h5_reset"
limit 7d "$d7" "$d7_reset"
[ -n "$limits" ] && line="${line}  ${limits}"

# ── lines changed this session ────────────────────────────────────────────
if [ -n "$added" ] || [ -n "$removed" ]; then
  line="${line}  ${c_add}+${added:-0}${R}/${c_rem}-${removed:-0}${R}"
fi

# ── session cost ──────────────────────────────────────────────────────────
if [ -n "$cost" ] && [ "$cost" != "0" ]; then
  printf -v costf "%.2f" "$cost" 2>/dev/null && line="${line}  ${c_mut}\$${costf}${R}"
fi

printf "%b" "$line"
