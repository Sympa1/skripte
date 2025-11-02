#!/bin/bash

# ============================================================================
# GitHub Sync Starter - Terminal-Wrapper für verschiedene Linux-Desktops
# ============================================================================

# Skript-Verzeichnis ermitteln (funktioniert auch bei Symlinks)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/github_sync_skript.py"

# Prüfen ob Python-Skript existiert
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Fehler: $PYTHON_SCRIPT nicht gefunden!"
    exit 1
fi

# Desktop-Umgebung erkennen (XDG_CURRENT_DESKTOP oder DESKTOP_SESSION)
DESKTOP="${XDG_CURRENT_DESKTOP:-$DESKTOP_SESSION}"

# Terminal-Emulatoren nach Desktop-Umgebung zuordnen
case "$DESKTOP" in
    *KDE*)
        # KDE Plasma - Konsole bleibt mit --hold offen
        TERM_CMD="konsole --hold -e"
        ;;
    *GNOME*|*Unity*)
        # GNOME/Unity - Terminal mit manueller Pause (read-Befehl)
        TERM_CMD="gnome-terminal -- bash -c"
        WRAP_CMD="; read -p 'Drücke Enter zum Schließen...'"
        ;;
    *XFCE*)
        # XFCE - Terminal bleibt mit --hold offen
        TERM_CMD="xfce4-terminal --hold -e"
        ;;
    *MATE*)
        # MATE Desktop - Terminal mit manueller Pause
        TERM_CMD="mate-terminal -- bash -c"
        WRAP_CMD="; read -p 'Drücke Enter zum Schließen...'"
        ;;
    *Cinnamon*)
        # Cinnamon (Linux Mint) - nutzt gnome-terminal
        TERM_CMD="gnome-terminal -- bash -c"
        WRAP_CMD="; read -p 'Drücke Enter zum Schließen...'"
        ;;
    *LXDE*|*LXQt*)
        # LXDE/LXQt - LXTerminal mit --command
        TERM_CMD="lxterminal --command"
        ;;
    *)
        # Unbekannter Desktop - Fallback-Logik verwenden
        TERM_CMD=""
        ;;
esac

# Funktion: Python-Skript im Terminal ausführen
run_in_terminal() {
    # Desktop-spezifisches Terminal gefunden?
    if [ -n "$TERM_CMD" ]; then
        if [ -n "$WRAP_CMD" ]; then
            # Terminal benötigt manuellen Pause-Befehl (GNOME, MATE, Cinnamon)
            $TERM_CMD "python3 '$PYTHON_SCRIPT'$WRAP_CMD"
        else
            # Terminal unterstützt --hold Flag (KDE, XFCE)
            $TERM_CMD python3 "$PYTHON_SCRIPT"
        fi
        return $?
    fi

    # Fallback: Verfügbare Terminals in Reihenfolge durchprobieren
    for term in konsole gnome-terminal xfce4-terminal mate-terminal lxterminal alacritty kitty xterm; do
        if command -v "$term" &> /dev/null; then
            case "$term" in
                konsole)
                    # KDE Konsole: --hold hält Terminal offen
                    konsole --hold -e python3 "$PYTHON_SCRIPT"
                    ;;
                gnome-terminal|mate-terminal)
                    # GNOME/MATE: Bash-Wrapper mit read-Pause
                    $term -- bash -c "python3 '$PYTHON_SCRIPT'; read -p 'Drücke Enter zum Schließen...'"
                    ;;
                xfce4-terminal)
                    # XFCE Terminal: --hold Option
                    xfce4-terminal --hold -e "python3 '$PYTHON_SCRIPT'"
                    ;;
                lxterminal)
                    # LXTerminal: --command mit Bash-Wrapper
                    lxterminal --command "bash -c \"python3 '$PYTHON_SCRIPT'; read -p 'Drücke Enter zum Schließen...'\""
                    ;;
                alacritty|kitty)
                    # Moderne GPU-beschleunigte Terminals
                    $term -e bash -c "python3 '$PYTHON_SCRIPT'; read -p 'Drücke Enter zum Schließen...'"
                    ;;
                xterm)
                    # Klassisches X Terminal: -hold Option
                    xterm -hold -e python3 "$PYTHON_SCRIPT"
                    ;;
            esac
            exit $?
        fi
    done

    # Letzter Fallback: Kein grafisches Terminal gefunden - im aktuellen Terminal ausführen
    echo "⚠ Kein grafisches Terminal gefunden. Ausführung im aktuellen Terminal:"
    python3 "$PYTHON_SCRIPT"
    read -p "Drücke Enter zum Schließen..."
}

# Terminal-Funktion ausführen
run_in_terminal