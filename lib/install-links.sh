#!/usr/bin/env bash
# Shared by the skills and mods installers; no work happens when this is sourced.

link_agent_item() {
    local target="$1" path="$2" check="$3"
    if [[ "$(readlink "$path" || true)" == "$target" ]]; then
        echo "ok       $path"
    elif $check; then
        echo "missing  $path -> $target"
        return 1
    elif [[ -e "$path" && ! -L "$path" ]]; then
        echo "skipped  $path is a real file or directory; move it aside and re-run"
        return 1
    elif mkdir -p "$(dirname "$path")" && ln -sfn "$target" "$path"; then
        echo "linked   $path -> $target"
    else
        echo "FAILED   $path"
        return 1
    fi
}

install_agent_links() {
    local root="$1" component="$2" check=false failed=0
    local source marker other_marker other_source dir name destination path target
    local -a destinations
    shift 2
    if [[ "$#" -gt 1 ]]; then
        echo "usage: $0 [--check]" >&2
        return 2
    fi
    case "${1:-}" in
        "") ;;
        --check) check=true ;;
        -h | --help) echo "usage: $0 [--check]"; return 0 ;;
        *) echo "usage: $0 [--check]" >&2; return 2 ;;
    esac
    case "$component" in
        skills)
            marker=SKILL.md
            other_source="$root/mods"
            other_marker=.claude-plugin/plugin.json
            destinations=("$HOME/.claude/skills" "$HOME/.agents/skills")
            ;;
        mods)
            marker=.claude-plugin/plugin.json
            other_source="$root/skills"
            other_marker=SKILL.md
            destinations=("$HOME/.claude/skills")
            ;;
        *) echo "unknown component: $component" >&2; return 2 ;;
    esac
    source="$root/$component"

    for dir in "$source"/*/; do
        # Ignore supporting files and unfinished folders, such as a mod without
        # its plugin manifest. A directory alone does not make an installable item.
        [[ -f "$dir/$marker" ]] || continue
        name="$(basename "$dir")"
        if [[ -f "$other_source/$name/$other_marker" ]]; then
            echo "conflict $name is both a skill and a mod; they share Claude's skills directory"
            failed=1
            continue
        fi
        for destination in "${destinations[@]}"; do
            link_agent_item "$source/$name" "$destination/$name" "$check" || failed=1
        done
    done

    # Remove broken links belonging to this component in this checkout only.
    for destination in "${destinations[@]}"; do
        for path in "$destination"/*; do
            [[ -L "$path" && ! -e "$path" ]] || continue
            target="$(readlink "$path")"
            [[ "$target" == "$source"/* ]] || continue
            if $check; then
                echo "stale    $path -> $target"
                failed=1
            elif rm "$path"; then
                echo "removed  $path, whose target is gone"
            else
                echo "FAILED   removing $path"
                failed=1
            fi
        done
    done

    return "$failed"
}
