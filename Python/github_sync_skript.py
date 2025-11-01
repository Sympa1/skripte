#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TODO: Skriptbeschreibung einfügen
"""

# TODO: Wenn der Commit nicht klappt, weil keine neuen Änderungen vorliegen,
#       sollte das Skript trotzdem erfolgreich durchlaufen und nicht mit
#       einem Fehler abbrechen.
import gc
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime


class Logger:
    """
    Context Manager für das Schreiben von Log-Einträgen in eine Datei.

    Diese Klasse ermöglicht das strukturierte Protokollieren von Nachrichten,
    Warnungen und Fehlern. Jeder Eintrag wird mit einem Zeitstempel versehen
    und kann mit einer individuellen Überschrift kategorisiert werden.

    Verwendung als Context Manager:
        with Logger() as log:
            log.write_to_log_file("Nachricht", "Überschrift")

    Attributes:
        _log_file_name (str): Pfad zur Log-Datei (default: "error.log")
    """

    def __init__(self, log_file_name: str = "error.log"):
        """
        Initialisiert den Logger mit einem Dateinamen.

        Args:
            log_file_name (str): Name/Pfad der Log-Datei.
                                 Default ist "error.log" im aktuellen Verzeichnis.

        Note:
            Das Präfix '_' markiert _log_file_name als protected (Konvention).
        """
        self._log_file_name = log_file_name

    def __enter__(self):
        """
        Wird beim Betreten des Context Managers aufgerufen.

        Ermöglicht die Verwendung der 'with'-Anweisung.

        Returns:
            Logger: Die Logger-Instanz selbst für die Verwendung im with-Block.

        Example:
            with Logger() as log:  # <- __enter__() wird hier aufgerufen
                log.write_to_log_file("Test")
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Wird beim Verlassen des Context Managers aufgerufen.

        Gibt Exception-Details in der Konsole aus, falls eine Exception
        im with-Block aufgetreten ist. Die Exception wird anschließend
        weitergegeben (nicht unterdrückt).

        Args:
            exc_type: Exception-Typ (z.B. ValueError, None wenn keine Exception)
            exc_val: Exception-Wert/Nachricht (z.B. "ungültiger Wert")
            exc_tb: Traceback-Objekt (Stacktrace der Exception)

        Returns:
            False: Exception wird weitergegeben (nicht unterdrückt).
                   True würde die Exception unterdrücken (nicht empfohlen!).

        Note:
            Kein Cleanup nötig, da die Log-Datei in write_to_log_file()
            bereits mit 'with open()' automatisch geschlossen wird.
        """
        # Prüfen, ob eine Exception aufgetreten ist
        if exc_type is not None:
            # Exception-Details rot formatiert in der Konsole ausgeben
            print(f"\033[31mException im Logger-Context: {exc_type.__name__}: {exc_val}\033[0m")

        # False = Exception wird weitergegeben (nicht unterdrücken)
        return False

    def write_to_log_file(self, message: str, headline: str = "Error"):
        """
        Schreibt einen formatierten Eintrag in die Log-Datei.

        Der Eintrag wird im Append-Modus ('a') ans Ende der Datei angefügt,
        sodass vorherige Einträge erhalten bleiben. Jeder Eintrag enthält:
        - Eine Überschrift (z.B. "Error", "Warning", "Info")
        - Einen Zeitstempel (Format: YYYY-MM-DD HH:MM:SS)
        - Die eigentliche Nachricht
        - Zwei Leerzeilen als Trenner zum nächsten Eintrag

        Args:
            message (str): Die zu protokollierende Nachricht.
            headline (str): Kategorisierung des Eintrags (default: "Error").
                           Beispiele: "Error", "Warning", "Info", "Debug"

        Example:
            log.write_to_log_file("Datei nicht gefunden", "Warning")

            # Erzeugt in error.log:
            # ===== Warning =====
            # 2025-01-19 14:30:15 - Datei nicht gefunden
            #

        Note:
            - Der Modus 'a' (append) stellt sicher, dass die Datei nicht
              überschrieben wird und jeder Aufruf einen neuen Eintrag anfügt.
            - UTF-8 Encoding gewährleistet korrekte Darstellung von Umlauten.
            - Die Datei wird automatisch durch 'with' geschlossen.
        """
        # Aktuellen Zeitstempel generieren
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Formatierte Log-Nachricht mit Überschrift, Zeitstempel und Nachricht erstellen
        log_entry = f"===== {headline} ===== \n{timestamp} - {message}\n\n"

        # Datei im Append-Modus öffnen und Eintrag hinzufügen
        # 'a' = append (anhängen, nicht überschreiben)
        # encoding='utf-8' = Umlaute und Sonderzeichen korrekt speichern
        # 'with' = Datei wird automatisch geschlossen, auch bei Fehlern
        with open(self._log_file_name, 'a', encoding='utf-8') as f:
            f.write(log_entry)


class EnvLoader:
    """
    Lädt und verwaltet Umgebungsvariablen aus einer .env-Datei.

    Diese Klasse ermöglicht das strukturierte Lesen von Konfigurationswerten
    aus einer .env-Datei. Die Variablen werden in einem internen Dictionary
    gespeichert und können über get_var() abgerufen werden.

    Unterstützte .env-Formate:
        KEY=value\n
        KEY="value"\n
        KEY='value'\n
        # Kommentarzeilen werden ignoriert

    Example:
        env = EnvLoader()
        if env.load_env_file('.env'):
            repo_path = env.get_var('REPO_PFAD_LIN')

    Attributes:
        _env_vars (dict): Dictionary zum Speichern der geladenen Variablen.
                         Key = Variablenname, Value = Variablenwert
    """

    def __init__(self):
        """
        Initialisiert den EnvLoader mit einem leeren Dictionary.

        Das Dictionary _env_vars wird verwendet, um alle geladenen
        Umgebungsvariablen aus der .env-Datei zu speichern.

        Note:
            Das Präfix '_' markiert _env_vars als protected (Konvention).
        """
        self._env_vars = {}

    def load_env_file(self, env_path: str) -> bool:
        """
        Die Methode liest die angegebene .env-Datei zeilenweise, parst
        Key-Value-Paare und speichert sie im internen Dictionary.
        Fehler werden in der Konsole ausgegeben und geloggt.

        Parsing-Regeln:
        - Leerzeilen werden ignoriert
        - Zeilen mit '#' am Anfang werden als Kommentare ignoriert
        - Format: KEY=VALUE (Leerzeichen um '=' werden entfernt)
        - Anführungszeichen (', ") um Values werden entfernt

        Args:
            env_path (str): Pfad zur .env-Datei (relativ oder absolut).
                           Beispiel: '.env', '/path/to/config.env'

        Returns:
            bool: True bei erfolgreichem Laden, False bei Fehler.

        Example:
            # .env-Datei:
            # REPO_PFAD_LIN=/home/user/repo
            # DEBUG="true"

            if env.load_env_file('.env'):
                print("Erfolgreich geladen!")

        Note:
            - Fehler werden rot in der Konsole ausgegeben
            - Warnings werden gelb ausgegeben
            - Erfolg wird grün ausgegeben
            - Alle Fehler werden zusätzlich in die Log-Datei geschrieben
        """
        if not os.path.exists(env_path):
            # Warnung in Gelb ausgeben
            print(f"\033[33mWARNUNG: .env-Datei nicht gefunden unter: {env_path}\033[0m")

            with Logger() as log:
                log.write_to_log_file(f".env-Datei nicht gefunden unter: {env_path}", "EnvLoader Warning")

            return False

        try:
            # .env-Datei mit UTF-8 Encoding öffnen
            # 'r' = read-only Modus
            # encoding='utf-8' = Umlaute und Sonderzeichen korrekt lesen
            with open(env_path, 'r', encoding='utf-8') as file:
                # Jede Zeile der Datei durchgehen
                for line in file:
                    # Leerzeichen/Tabs am Anfang und Ende entfernen
                    line = line.strip()

                    # Prüfen, ob Zeile gültig ist:
                    # - Nicht leer
                    # - Kein Kommentar (startet nicht mit '#')
                    # - Enthält '=' (Key-Value-Trenner)
                    if line and not line.startswith('#') and '=' in line:
                        # Zeile bei erstem '=' in Key und Value aufteilen
                        # maxsplit=1 verhindert, dass '=' im Value selbst als Trenner gilt
                        key, value = line.split('=', 1)

                        # Leerzeichen um Key und Value entfernen
                        key = key.strip()

                        # Leerzeichen entfernen und Anführungszeichen (', ") am Anfang/Ende entfernen
                        # strip('"').strip("'") entfernt beide Arten von Anführungszeichen
                        value = value.strip().strip('"').strip("'")

                        # Key-Value-Paar im Dictionary speichern
                        self._env_vars[key] = value
            return True

        except Exception as e:
            # Fehler beim Lesen der Datei (z.B. Encoding-Problem, Zugriffsverweigerung)
            # Fehlermeldung rot in der Konsole ausgeben
            print(f"\033[31mFEHLER beim Lesen der .env-Datei: {e}\033[0m")

            # Fehler in Log-Datei schreiben
            with Logger() as log:
                log.write_to_log_file(f"FEHLER beim Lesen der .env-Datei:\n{e}", "EnvLoader Error")

            return False

    def get_var(self, key: str, default: str = None) -> str | None:
        """
        Gibt den Wert einer geladenen Umgebungsvariable zurück.

        Diese Methode ermöglicht den sicheren Zugriff auf Variablen,
        die mit load_env_file() geladen wurden. Wenn die Variable nicht
        existiert, wird ein optionaler Standardwert zurückgegeben.

        Args:
            key (str): Name der Umgebungsvariable (z.B. 'REPO_PFAD_LIN').
            default (str, optional): Standardwert, falls Variable nicht existiert.
                                    Default ist None.

        Returns:
            str | None: Wert der Variable oder default-Wert.

        Example:
            # Mit Standardwert:
            repo_path = env.get_var('REPO_PFAD_LIN', '/default/path')

            # Ohne Standardwert:
            debug_mode = env.get_var('DEBUG')
            if debug_mode is None:
                print("DEBUG nicht gesetzt")

        Note:
            - Gibt None zurück, wenn die Variable nicht existiert und kein
              default-Wert angegeben wurde.
            - Es wird nicht geprüft, ob load_env_file() erfolgreich war.
              Bei leerem Dictionary wird immer default zurückgegeben.
        """
        # Dictionary.get() gibt entweder den Wert für den key zurück oder default, falls der key nicht existiert
        return self._env_vars.get(key, default)


class GitSync:
    """
    Diese Klasse implementiert einen sicheren Git-Sync-Prozess:
    1. Pull (Remote-Änderungen holen)
    2. Add (Alle Änderungen stagen)
    3. Commit (Änderungen committen)
    4. Push (Änderungen hochladen)

    Die Klasse verwendet subprocess.run() um Git-Befehle auszuführen und
    erfasst stdout/stderr für detailliertes Feedback. Fehler werden sowohl
    in der Konsole (farbig) als auch in einer Log-Datei protokolliert.

    Verwendung:
        git = GitSync('/pfad/zum/repo')
        git.sync(commit_message='Update')

    Attributes:
        _repo_path (Path): Pfad zum Git-Repository als Path-Objekt.
                          Das Präfix '_' markiert es als protected.

    Raises:
        ValueError: Wenn der angegebene Repository-Pfad nicht existiert.

    Note:
        - Alle Git-Befehle werden im Repository-Verzeichnis (_repo_path) ausgeführt
        - Die Klasse geht davon aus, dass Git installiert und konfiguriert ist
        - Authentifizierung (SSH/HTTPS) muss bereits eingerichtet sein
    """

    def __init__(self, repo_path: str):
        """
        Initialisiert GitSync mit dem Repository-Pfad.

        Konvertiert den übergebenen String-Pfad in ein Path-Objekt und
        validiert die Existenz des Verzeichnisses. Dies verhindert, dass
        Git-Befehle auf nicht existierenden Pfaden ausgeführt werden.

        Args:
            repo_path (str): Pfad zum Git-Repository (relativ oder absolut).
                            Beispiele:
                            - Relativ: './my-repo' oder 'repos/project'
                            - Absolut: '/home/user/repos/project'

        Raises:
            ValueError: Wenn der Pfad nicht existiert.
                       Die Exception wird mit einer aussagekräftigen
                       Fehlermeldung geworfen, die den fehlenden Pfad enthält.

        Example:
            # Absoluter Pfad:
            git = GitSync('/home/user/my-repo')

            # Relativer Pfad:
            git = GitSync('./repos/project')

        Note:
            - Path() aus pathlib bietet plattformübergreifende Pfadoperationen
            - exists() prüft nur die Existenz, nicht ob es ein Git-Repo ist
            - Git-Validierung erfolgt erst bei der Ausführung von Git-Befehlen
        """
        # String-Pfad in Path-Objekt konvertieren für bessere Pfadoperationen
        self._repo_path = Path(repo_path)

        # Prüfen, ob der Pfad existiert (Verzeichnis oder Datei)
        if not self._repo_path.exists():
            # ValueError werfen mit aussagekräftiger Fehlermeldung
            # Diese Exception sollte vom Aufrufer gefangen werden
            raise ValueError(f"Repository-Pfad existiert nicht: {repo_path}")

    def _run_git_command(self, command: list[str]) -> tuple[bool, str, str]:
        """
        Führt einen Git-Befehl aus und gibt das Ergebnis zurück.

        Diese zentrale Hilfsmethode kapselt subprocess.run() für alle
        Git-Operationen. Sie führt den Befehl im Repository-Verzeichnis aus,
        erfasst stdout und stderr und gibt strukturierte Ergebnisse zurück.

        Das Präfix '_' markiert diese Methode als intern (nicht für externe Nutzung).

        Args:
            command (list[str]): Git-Befehl als Liste von Strings.
                                Der erste String ist immer 'git', gefolgt von
                                Subcommand und Optionen.
                                Beispiele:
                                - ['git', 'status']
                                - ['git', 'pull', 'origin', 'main']
                                - ['git', 'commit', '-m', 'message']

        Returns:
            tuple[bool, str, str]: Tuple mit drei Elementen:
                - bool: True bei Erfolg (returncode 0), False bei Fehler
                - str: Standardausgabe (stdout) des Git-Befehls
                - str: Fehlerausgabe (stderr) des Git-Befehls

        Example:
            success, output, error = self._run_git_command(['git', 'status'])
            if success:
                print(f"Git Status: {output}")
            else:
                print(f"Fehler: {error}")

        Note:
            - cwd=self._repo_path führt den Befehl im Repository-Ordner aus
            - capture_output=True erfasst stdout und stderr getrennt
            - text=True gibt Strings statt Bytes zurück (encoding='utf-8')
            - check=False verhindert Exception bei Non-Zero-Exit-Code
            - Wir prüfen returncode manuell für bessere Fehlerkontrolle
            - Exceptions (z.B. FileNotFoundError wenn Git fehlt) werden gefangen

        Raises:
            Keine Exception nach außen. Fehler werden als Tuple zurückgegeben.
        """
        try:
            # subprocess.run() führt den Befehl aus
            result = subprocess.run(
                command,                   # Git-Befehl als Liste
                cwd=self._repo_path,       # Working Directory = Repository-Pfad
                capture_output=True,       # stdout und stderr erfassen
                text=True,                 # String-Output statt Bytes
                check=False                # Keine Exception bei Non-Zero-Exit
            )

            # returncode == 0 bedeutet Erfolg bei Unix-Tools
            success = result.returncode == 0

            # Tuple mit (Erfolg, Stdout, Stderr) zurückgeben
            return success, result.stdout, result.stderr

        except Exception as e:
            # Exception (z.B. Git nicht installiert, Pfad nicht zugänglich)
            # Als Fehler-Tuple zurückgeben: (False, "", Exception-Message)
            return False, "", str(e)

    def pull(self) -> bool:
        """
        Holt Remote-Änderungen mit git pull.

        Führt 'git pull' aus, um Änderungen vom Remote-Repository zu holen
        und mit dem lokalen Branch zu mergen. Dies ist der erste Schritt
        im Sync-Workflow und verhindert Merge-Konflikte beim späteren Push.

        Der Befehl holt Änderungen vom konfigurierten Remote (meist 'origin')
        und merged sie automatisch in den aktuellen Branch.

        Returns:
            bool: True bei erfolgreichem Pull, False bei Fehler.
                 Mögliche Fehlerursachen:
                 - Keine Internetverbindung
                 - Remote-Repository nicht erreichbar
                 - Merge-Konflikte (erfordern manuelle Auflösung)
                 - Keine Remote-Tracking-Branch konfiguriert

        Example:
            if not git.pull():
                print("Pull fehlgeschlagen!")
                return False

        Note:
            - Fehler werden rot (\033[31m) in der Konsole ausgegeben
            - Fehler werden zusätzlich in die Log-Datei geschrieben
            - Erfolg wird grün (\033[32m) ausgegeben
            - Bei Merge-Konflikten stoppt der Pull und gibt False zurück
            - 🔄 Emoji als visueller Indikator für laufende Operation
            - ✓ / ✗ als Erfolgs-/Fehler-Indikatoren
        """
        # Benutzer-Feedback: Operation gestartet
        print("🔄 Pulling remote changes...")

        # Git-Pull-Befehl ausführen
        success, output, error = self._run_git_command(['git', 'pull'])

        if success:
            # Erfolg: Grüne Ausgabe mit Git-Output
            # strip() entfernt Leerzeilen am Ende
            print(f"\033[32m✓ Pull erfolgreich:\033[0m {output.strip()}")
            return True
        else:
            # Fehler: Rote Ausgabe mit Git-Error
            print(f"\033[31m✗ Pull fehlgeschlagen:\033[0m {error.strip()}")

            # Fehler in Log-Datei schreiben für spätere Analyse
            with Logger() as log:
                log.write_to_log_file(f"Git Pull Fehler:\n{error}", "GitSync Error")
            return False

    def add_all(self) -> bool:
        """
        Staged alle Änderungen mit git add .

        Führt 'git add .' aus, um alle geänderten, neuen und gelöschten
        Dateien für den nächsten Commit vorzubereiten. Der Punkt '.' bedeutet
        "alle Änderungen im aktuellen Verzeichnis und Unterverzeichnissen".

        Was wird gestaged:
        - Geänderte Dateien (modified)
        - Neue Dateien (untracked)
        - Gelöschte Dateien (deleted)
        - Umbenannte Dateien (renamed)

        Was wird NICHT gestaged:
        - Dateien in .gitignore
        - Bereits committete, unveränderte Dateien

        Returns:
            bool: True bei erfolgreichem Staging, False bei Fehler.
                 Fehler sind selten, können aber auftreten bei:
                 - Dateisystem-Problemen
                 - Ungültigen Dateinamen
                 - Fehlenden Berechtigungen

        Example:
            if not git.add_all():
                print("Staging fehlgeschlagen!")
                return False

        Note:
            - 'git add .' wirkt rekursiv auf alle Unterverzeichnisse
            - .gitignore-Einträge werden automatisch respektiert
            - Bei leerem Repository (keine Änderungen) ist der Befehl trotzdem erfolgreich
            - ➕ Emoji als visueller Indikator für Add-Operation
            - Ausgabe ist kurz, da 'git add .' normalerweise keine Ausgabe produziert
        """
        # Benutzer-Feedback: Operation gestartet
        print("➕ Adding all changes...")

        # Git-Add-Befehl ausführen
        # '.' bedeutet: alle Änderungen im Repository
        success, output, error = self._run_git_command(['git', 'add', '.'])

        if success:
            # Erfolg: Kurze grüne Bestätigung
            # Keine detaillierte Ausgabe nötig, da 'git add .' meist silent ist
            print("\033[32m✓ Changes staged\033[0m")
            return True
        else:
            # Fehler: Rote Ausgabe mit Git-Error
            print(f"\033[31m✗ Add fehlgeschlagen:\033[0m {error.strip()}")

            # Fehler in Log-Datei schreiben
            with Logger() as log:
                log.write_to_log_file(f"Git Add Fehler:\n{error}", "GitSync Error")
            return False

    def commit(self, message: str) -> bool:
        """
        Committed gestagede Änderungen mit git commit.

        Führt 'git commit' mit der angegebenen Nachricht aus und speichert
        alle gestageden Änderungen als neuen Commit im lokalen Repository.

        Ein Commit erstellt einen Snapshot des aktuellen Zustands aller
        gestageden Dateien mit einem Zeitstempel und Autor-Informationen.

        Spezialfall: Wenn keine Änderungen zum Committen vorhanden sind
        (alle Dateien bereits committed oder nichts gestaged), gibt Git
        eine entsprechende Meldung aus. Dies wird als Erfolg behandelt,
        da es kein Fehler ist.

        Args:
            message (str): Commit-Nachricht die beschreibt, was geändert wurde.
                          Beispiele:
                          - 'Update files'
                          - 'Fix bug in login'
                          - 'Automatischer Sync vom 2025-01-19'

        Returns:
            bool: True bei erfolgreichem Commit oder wenn nichts zu committen ist,
                 False bei echten Fehlern.

        Example:
            if not git.commit('Daily backup'):
                print("Commit fehlgeschlagen!")
                return False

        Note:
            - Git-Config muss user.name und user.email enthalten
            - "nothing to commit" ist KEIN Fehler, sondern erwartetes Verhalten
            - Dies wird als Warnung (gelb) ausgegeben, gibt aber True zurück
            - Die Commit-Message sollte aussagekräftig sein für spätere Nachvollziehbarkeit
            - 💾 Emoji als visueller Indikator für Commit-Operation
        """
        # Benutzer-Feedback: Operation gestartet mit Commit-Message
        print(f"💾 Committing changes with message: '{message}'...")

        # Git-Commit-Befehl ausführen
        # -m = Message-Flag, gefolgt von der Commit-Nachricht
        success, output, error = self._run_git_command(['git', 'commit', '-m', message])

        if success:
            # Erfolg: Grüne Ausgabe mit Git-Output (enthält Commit-Hash und Statistik)
            print(f"\033[32m✓ Commit erfolgreich:\033[0m {output.strip()}")
            return True

        # Spezialfall: Nichts zu committen (kein Fehler!)
        # Git gibt "nothing to commit" in stdout ODER stderr aus
        elif "nothing to commit" in output.lower() or "nothing to commit" in error.lower():
            # Gelbe Warnung ausgeben (kein Fehler, aber wichtige Info)
            print("\033[33m⚠ Keine Änderungen zum Committen\033[0m")
            # True zurückgeben, da dies kein Fehler ist
            return True

        else:
            # Echter Fehler: Rote Ausgabe
            # Mögliche Ursachen: Fehlende Git-Config, ungültige Zeichen in Message
            print(f"\033[31m✗ Commit fehlgeschlagen:\033[0m {error.strip()}")

            # Fehler in Log-Datei schreiben
            with Logger() as log:
                log.write_to_log_file(f"Git Commit Fehler:\n{error}", "GitSync Error")
            return False

    def push(self) -> bool:
        """
        Pusht lokale Commits zum Remote-Repository mit git push.

        Führt 'git push' aus, um alle lokalen Commits, die noch nicht im
        Remote-Repository sind, hochzuladen. Dies ist der letzte Schritt
        im Sync-Workflow und macht die Änderungen für andere zugänglich.

        Der Befehl pusht den aktuellen Branch zum konfigurierten Remote
        (meist 'origin'). Git verwendet dabei die Remote-Tracking-Branch-
        Konfiguration (z.B. main → origin/main).

        Returns:
            bool: True bei erfolgreichem Push, False bei Fehler.
                 Häufige Fehlerursachen:
                 - Keine Internetverbindung
                 - Fehlende Push-Berechtigung (SSH-Key, Access Token)
                 - Remote ist ahead (jemand hat gepusht, Pull nötig)
                 - Branch existiert nicht im Remote
                 - Merge-Konflikt beim Remote

        Example:
            if not git.push():
                print("Push fehlgeschlagen!")
                return False

        Note:
            - Authentifizierung muss bereits eingerichtet sein (SSH oder HTTPS)
            - Bei "remote is ahead" Fehler: zuerst pullen, dann erneut pushen
            - Der Push kann fehlschlagen, wenn Remote-Änderungen vorhanden sind
            - ⬆️ Emoji als visueller Indikator für Upload-Operation
            - Push-Fehler sollten immer untersucht werden (siehe Log)
        """
        # Benutzer-Feedback: Operation gestartet
        print("⬆️  Pushing changes to remote...")

        # Git-Push-Befehl ausführen
        success, output, error = self._run_git_command(['git', 'push'])

        if success:
            # Erfolg: Grüne Ausgabe mit Git-Output (enthält Branch-Info)
            print(f"\033[32m✓ Push erfolgreich:\033[0m {output.strip()}")
            return True
        else:
            # Fehler: Rote Ausgabe mit Git-Error
            # Häufig: "remote is ahead", "authentication failed", "no upstream"
            print(f"\033[31m✗ Push fehlgeschlagen:\033[0m {error.strip()}")

            # Fehler in Log-Datei schreiben für spätere Analyse
            with Logger() as log:
                log.write_to_log_file(f"Git Push Fehler:\n{error}", "GitSync Error")
            return False

    def sync(self, commit_message: str = "Auto-sync") -> bool:
        """
        Führt einen vollständigen Sync-Workflow aus.

        Diese Methode orchestriert alle vier Git-Operationen in der richtigen
        Reihenfolge für einen sicheren Sync-Prozess. Sie ist die Hauptmethode
        der GitSync-Klasse und sollte für regelmäßige Updates verwendet werden.

        Workflow-Schritte:
        1. Pull: Remote-Änderungen holen
           → Verhindert Konflikte beim Push
           → Holt Änderungen von anderen Team-Mitgliedern

        2. Add: Alle lokalen Änderungen stagen
           → Bereitet alle Änderungen für Commit vor
           → Inkludiert neue, geänderte und gelöschte Dateien

        3. Commit: Änderungen lokal committen
           → Erstellt Snapshot mit Zeitstempel
           → Speichert Änderungen im lokalen Repository

        4. Push: Änderungen zum Remote hochladen
           → Macht Änderungen für andere verfügbar
           → Synchronisiert lokales und Remote-Repository

        Der Workflow stoppt beim ersten Fehler (Fail-Fast-Prinzip).
        Alle nachfolgenden Schritte werden übersprungen.

        Args:
            commit_message (str): Commit-Nachricht für den Commit-Schritt.
                                 Default: 'Auto-sync'
                                 Kann beliebig angepasst werden, z.B. mit Zeitstempel.

        Returns:
            bool: True wenn ALLE Schritte erfolgreich, False bei erstem Fehler.

        Example:
            # Mit Standard-Message:
            if git.sync():
                print('Sync erfolgreich!')

            # Mit eigener Message:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if git.sync(f'Daily backup {timestamp}'):
                print('Backup erfolgreich!')

        Note:
            - Der Workflow ist fail-fast: Erster Fehler = Abbruch
            - Fehler werden in der Konsole (rot) und im Log ausgegeben
            - Pull zuerst ist wichtig! Verhindert Push-Konflikte
            - Bei "nothing to commit" wird der Workflow fortgesetzt
            - Die Methode gibt detailliertes visuelles Feedback mit Emojis
            - Separatoren (===) erleichtern die Lesbarkeit im Terminal
        """
        # Visueller Separator: Sync-Start markieren
        print("\n" + "=" * 50)
        print("🔄 Starte Git-Sync-Workflow...")
        print("=" * 50 + "\n")

        # Schritt 1: Pull (Remote-Änderungen holen)
        # → WICHTIG: Pull zuerst! Verhindert Konflikte beim Push
        if not self.pull():
            # Pull fehlgeschlagen → Workflow abbrechen
            # Rote Fehlerausgabe mit Emoji für bessere Sichtbarkeit
            print("\n\033[31m❌ Sync abgebrochen (Pull fehlgeschlagen)\033[0m\n")
            return False  # Fail-Fast: Kein weiterer Schritt wird ausgeführt

        # Schritt 2: Add (Alle Änderungen stagen)
        # → Bereitet alle Änderungen für den Commit vor
        if not self.add_all():
            # Add fehlgeschlagen → Workflow abbrechen
            print("\n\033[31m❌ Sync abgebrochen (Add fehlgeschlagen)\033[0m\n")
            return False

        # Schritt 3: Commit (Änderungen committen)
        # → Speichert Änderungen lokal mit der angegebenen Message
        # → Bei "nothing to commit" gibt commit() True zurück (kein Fehler)
        if not self.commit(commit_message):
            # Commit fehlgeschlagen → Workflow abbrechen
            print("\n\033[31m❌ Sync abgebrochen (Commit fehlgeschlagen)\033[0m\n")
            return False

        # Schritt 4: Push (Änderungen hochladen)
        # → Macht lokale Commits im Remote verfügbar
        # → Kann fehlschlagen wenn Remote ahead ist (Pull erforderlich)
        if not self.push():
            # Push fehlgeschlagen → Workflow abbrechen
            print("\n\033[31m❌ Sync abgebrochen (Push fehlgeschlagen)\033[0m\n")
            return False

        # Alle Schritte erfolgreich! Erfolgs-Ausgabe mit visuellem Feedback
        print("\n" + "=" * 50)
        print("\033[32m✓ Git-Sync erfolgreich abgeschlossen!\033[0m")
        print("=" * 50 + "\n")

        # True = Gesamter Workflow erfolgreich
        return True

def main():
    env = EnvLoader()

    if not env.load_env_file('.env'):
        print("\033[31mFEHLER: .env-Datei konnte nicht geladen werden.\033[0m")
        sys.exit(1)

    repo_path = env.get_var('REPO_PFAD_LIN')

    if repo_path is None:
        print("\033[31mFEHLER: REPO_PFAD_LIN nicht in der .env-Datei gefunden.\033[0m")
        sys.exit(1)

    # Git-Sync durchführen
    git = GitSync(repo_path)

    if git.sync("Automatischer Sync vom " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')):
        print("\033[32m✓ Repository erfolgreich synchronisiert!\033[0m")
    else:
        print("\033[31m✗ Sync fehlgeschlagen - siehe Logs für Details\033[0m")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    finally:
        # Terminal offen halten
        input("\nDrücke Enter zum Beenden...")
