#!/usr/bin/env bash
# Installs Homebrew, the taps, formulae and casks in the Brewfile, and a few tools that come from
# their own installers, for a new Mac. A plain run installs what is missing, without upgrading the
# rest, and reports what is installed here but isn't in the Brewfile. --check only reports, and
# --pull rewrites the Brewfile from what is installed here, to review and commit.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mode="${1:-}"
case "$mode" in
    "" | --check | --pull) ;;
    *) echo "usage: $0 [--check | --pull]" >&2; exit 2 ;;
esac
failed=0
stale=0
brewfile="$root/Brewfile"
# This repo is public, so what shouldn't be listed in it is in a second Brewfile, outside it.
private="$HOME/.Brewfile.private"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# A shell that was open before Homebrew was installed doesn't have it on PATH.
brew="$(command -v brew || echo /opt/homebrew/bin/brew)"
command -v brew >/dev/null || stale=1
if [[ -x "$brew" ]]; then
    echo "ok       Homebrew"
elif [[ -n "$mode" ]]; then
    echo "missing  Homebrew"
    exit 1
else
    # Homebrew's installer says what it will do and waits for a go-ahead. It also installs the
    # Command Line Tools.
    installer="$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    /bin/bash -c "$installer"
    echo "added    Homebrew"
fi

# What is installed here, written the way the Brewfile is.
installed="$tmp/installed"
"$brew" bundle dump --file="$installed" --tap --formula --cask

# The entries of a Brewfile without their description comments, so that two compare as sets.
entries() {
    sed '/^#/d; /^$/d' "$1" | LC_ALL=C sort -u
}

# $1 without the entries that $2 also has, or the description comments above them. It goes by an
# entry's kind and name, so that one whose options have changed is still left out.
without() {
    awk '
        FILENAME == ARGV[1] { if (match($0, /^[a-z]+ "[^"]*"/)) drop[substr($0, RSTART, RLENGTH)]; next }
        /^#/ { held = held $0 "\n"; next }
        { if (!(match($0, /^[a-z]+ "[^"]*"/) && (substr($0, RSTART, RLENGTH) in drop))) printf "%s%s\n", held, $0; held = "" }
    ' "$2" "$1"
}

# Prints each line of $2 with the status $1, and fails the run.
report() {
    local line
    [[ -n "$2" ]] || return 0
    while IFS= read -r line; do
        printf '%-8s %s\n' "$1" "$line"
    done <<<"$2"
    failed=1
}

if [[ "$mode" == --pull && ! -e "$private" ]]; then
    # Without it, everything installed here would go into the Brewfile, and from there to GitHub.
    echo "REFUSED  $private isn't there, so --pull can't tell what to keep out of this public repo; copy it from the other Mac, or make an empty one"
    failed=1
elif [[ "$mode" == --pull ]]; then
    without "$installed" "$private" >"$tmp/public"
    if cmp -s "$tmp/public" "$brewfile"; then
        echo "ok       Brewfile"
    else
        cat "$tmp/public" >"$brewfile"
        echo "pulled   Brewfile"
    fi
else
    [[ -e "$private" ]] || private=/dev/null
    cat "$brewfile" "$private" >"$tmp/wanted"
    missing="$(LC_ALL=C comm -23 <(entries "$tmp/wanted") <(entries "$installed"))"
    unlisted="$(LC_ALL=C comm -13 <(entries "$tmp/wanted") <(entries "$installed"))"
    if [[ -z "$missing$unlisted" ]]; then
        echo "ok       Brewfile"
    elif [[ "$mode" == --check ]]; then
        report missing "$missing"
    elif [[ -n "$missing" ]]; then
        # Running this script is the go-ahead, so brew isn't left to ask for another. The installs
        # run as one brew command, and --verbose shows its output as it goes.
        HOMEBREW_NO_ASK=1 "$brew" bundle install --file="$tmp/wanted" --no-upgrade --verbose || failed=1
    fi
    report unlisted "$unlisted"
fi

# Homebrew doesn't load a formula or cask from a tap it doesn't trust, so the dump leaves those out
# without saying so.
distrusted="$("$brew" untrust | sed 's/^ *//')"
for kind in formula cask; do
    while IFS= read -r name; do
        echo "skipped  $name isn't trusted, so the Brewfile can't list it. Run: brew trust --$kind $name"
        failed=1
    done < <("$brew" list "--$kind" --full-name | grep -Fx -e "$distrusted")
done

# Installs $1 with the script at $3, run by the rest of the arguments, unless $2 is already there.
# The script is fetched whole before any of it runs.
tool() {
    local name="$1" path="$2" url="$3" script
    shift 3
    if [[ -e "$path" ]]; then
        echo "ok       $name"
    elif [[ -n "$mode" ]]; then
        echo "missing  $name"
        failed=1
    elif script="$(curl --proto '=https' --tlsv1.2 -fsSL "$url")" && "$@" <<<"$script"; then
        echo "added    $name"
        stale=1
    else
        echo "FAILED   $name"
        failed=1
    fi
}

# These keep themselves up to date, so they come from their own installers, not from Homebrew.
tool rustup "$HOME/.cargo/bin/rustup" https://sh.rustup.rs sh -s -- -y
tool "Claude Code" "$HOME/.local/bin/claude" https://claude.ai/install.sh bash
tool Codex "$HOME/.local/bin/codex" https://chatgpt.com/codex/install.sh sh
tool herdr "$HOME/.local/bin/herdr" https://herdr.dev/install.sh sh
# Its installer also writes a ~/.zshrc, unless one is there: --keep-zshrc leaves that one alone.
tool "Oh My Zsh" "$HOME/.oh-my-zsh/oh-my-zsh.sh" \
    https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh \
    sh -s -- --unattended --keep-zshrc

if [[ -z "$mode" && "$stale" == 1 ]]; then
    echo "note     open a new terminal, so that what was installed is on PATH"
fi

exit "$failed"
