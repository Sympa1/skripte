#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/github_sync_skript.py"

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Fehler: $PYTHON_SCRIPT nicht gefunden!" >&2
    exit 1
fi

ARG_STR=""
if [ "$#" -gt 0 ]; then
    ARG_STR="$(printf " %q" "$@")"
fi

PY_CMD="$(printf "%q" "python3") $(printf "%q" "$PYTHON_SCRIPT")$ARG_STR"

DESKTOP="${XDG_CURRENT_DESKTOP:-$DESKTOP_SESSION}"

case "$DESKTOP" in
    *KDE*)
        if command -v konsole &> /dev/null; then
            eval "konsole -e bash -c \"$PY_CMD\""
            exit $?
        fi
        ;;
    *GNOME*|*Unity*|*Cinnamon*)
        if command -v gnome-terminal &> /dev/null; then
            eval "gnome-terminal -- bash -c \"$PY_CMD\""
            exit $?
        fi
        ;;
    *XFCE*)
        if command -v xfce4-terminal &> /dev/null; then
            eval "xfce4-terminal -e bash -c \"$PY_CMD\""
            exit $?
        fi
        ;;
    *MATE*)
        if command -v mate-terminal &> /dev/null; then
            eval "mate-terminal -- bash -c \"$PY_CMD\""
            exit $?
        fi
        ;;
    *LXDE*|*LXQt*)
        if command -v lxterminal &> /dev/null; then
            eval "lxterminal --command \"bash -c \\\"$PY_CMD\\\"\""
            exit $?
        fi
        ;;
esac

for term in konsole gnome-terminal xfce4-terminal mate-terminal lxterminal alacritty kitty xterm; do
    if command -v "$term" &> /dev/null; then
        case "$term" in
            konsole)
                eval "konsole -e bash -c \"$PY_CMD\""
                ;;
            gnome-terminal|mate-terminal)
                eval "$term -- bash -c \"$PY_CMD\""
                ;;
            xfce4-terminal)
                eval "xfce4-terminal -e bash -c \"$PY_CMD\""
                ;;
            lxterminal)
                eval "lxterminal --command \"bash -c \\\"$PY_CMD\\\"\""
                ;;
            alacritty|kitty)
                eval "$term -e bash -c \"$PY_CMD\""
                ;;
            xterm)
                eval "xterm -e bash -c \"$PY_CMD\""
                ;;
        esac
        exit $?
    fi
done

echo "⚠ Kein grafisches Terminal gefunden. Ausführung im aktuellen Terminal:"
eval "$PY_CMD"
