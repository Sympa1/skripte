# Skripte-Repository

Dieses Repository enthält eine Sammlung von Skripten zur Automatisierung häufiger Routineaufgaben. Ziel ist die
Vereinfachung wiederkehrender Abläufe. Pfade und sensible Einstellungen werden in externen ` .env `-Dateien gespeichert
und nicht versioniert.

Die Skripte sind nach Programmiersprache sortiert. Starter-Skripte, die ein Terminal öffnen und das jeweilige Skript
ausführen sind namentlich dem jeweiligen Skript zugeordnet und befinden sich im selben Verzeichnis.

## Verzeichnisstruktur

```
.
├── bash/
│   └── PLACEHOLDER.sh
├── powershell/
│   └── PLACEHOLDER.ps1
├── python/
│   ├── github_sync_skript.py
│   └── starter_github_sync_skript.sh
├── .gitignore
├── .env
├── LICENSE
└── README.md
```

## Installation

1. Klone dieses Repository:
   ```
   git clone https://github.com/Sympa1/Skripte
   ```

2. Navigiere in das Verzeichnis:
   ```
   cd Skripte
   ```

3. Erstelle nach der untenstehenden Anleitung ein `.env` File.

## Umgebungsvariablen

Die Skripte verwenden `.env`-Dateien, um Pfade und andere Konfigurationen zu speichern. Diese werden nicht im Repository gespeichert.

Beispiel für eine `.env`-Datei für Git-Skripte:
```
# Repository-Pfad
REPO_PFAD_WIN=C:/Pfad/zum/Repository
REPO_PFAD_LIN="/home/user/"
```

## Verwendung

### PowerShell Git-Skripte

Um ein Repository zu pullen:
```powershell
./PowerShell/gitPull.ps1
```

Um ein Repository zu pushen:
```powershell
./PowerShell/gitPush.ps1
```

### Bash Git-Skripte

Um ein Repository zu pullen:
```bash
./Bash/gitPull.sh
```

Um ein Repository zu pushen:
```bash
./Bash/gitPush.sh
```
## .gitignore

Die folgende `.gitignore`-Datei wird verwendet:

```
# Umgebungsvariablen-Dateien
.env
**/.env
```

## Lizenz

Dieses Projekt ist unter der GPL-3.0 lizenziert - siehe die [LICENSE](LICENSE)-Datei für Details.
