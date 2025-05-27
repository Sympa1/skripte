#!/usr/bin/bash

# Pull-Script (gitPull.sh)

# Einlesen der .env Datei
SCRIPT_VERZEICHNIS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_PFAD="$SCRIPT_VERZEICHNIS/../.env"
REPO_PFAD="."

if [ -f "$ENV_PFAD" ]; then
    
    # Suche nach REPO_PATH_LIN
    REPO_PFAD_LIN=$(grep "^\s*REPO_PFAD_LIN\s*=" "$ENV_PFAD" 2>/dev/null)
    if [ -n "$REPO_PFAD_LIN" ]; then
        REPO_PFAD=$(echo "$REPO_PFAD_LIN" | sed 's/^\s*REPO_PFAD_LIN\s*=\s*\(.*\)\s*$/\1/' | tr -d '"' | tr -d "'" | xargs)
        echo "Repo-Pfad gefunden: $REPO_PFAD"
    else
        echo "REPO_PATH_LIN nicht in .env gefunden"
    fi
else
    echo -e "\033[33mWARNUNG: .env-Datei nicht gefunden unter: $ENV_PFAD\033[0m"
fi

# Ins Repo-Verzeichnis wechseln
if [ -d "$REPO_PFAD" ]; then
    echo "Wechsle in Verzeichnis: $REPO_PFAD"
    cd "$REPO_PFAD" || {
        echo -e "\033[0;31mFehler beim Wechsel in das Verzeichnis $REPO_PFAD!\033[0m"
        exit 1
    }
else
    echo -e "\033[0;31mVerzeichnis $REPO_PFAD existiert nicht!\033[0m"
    exit 1
fi

# Git Pull ausführen mit expliziter Merge-Strategie
echo -e "\033[0;34mPull aus dem Repository...\033[0m"
pull_ausgabe=$(git pull --no-rebase 2>&1)
pull_exit_code=$?

echo "Pull Ausgabe: $pull_ausgabe"

# Prüfe beide möglichen Ausgaben (deutsch und englisch)
if [[ $pull_ausgabe == *"Bereits aktuell"* ]] || [[ $pull_ausgabe == *"Already up to date"* ]]; then
    echo -e "\033[0;34mBereits aktuell.\033[0m"
elif [[ $pull_exit_code -eq 0 ]]; then
    echo -e "\033[0;34mPull erfolgreich abgeschlossen!\033[0m"
else
    echo -e "\033[0;31mPull fehlgeschlagen! Exit-Code: $pull_exit_code\033[0m"
    exit 1
fi
