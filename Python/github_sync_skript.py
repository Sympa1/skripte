#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TODO: Skriptbeschreibung einfügen
"""
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


def main():
    env = EnvLoader()

    if not env.load_env_file('.env'):
        print("\033[31mFEHLER: .env-Datei konnte nicht geladen werden.\033[0m")
        sys.exit(1)

    repo_path = env.get_var('REPO_PFAD_LIN')

    if repo_path is None:
        print("\033[31mFEHLER: REPO_PFAD_LIN nicht in der .env-Datei gefunden.\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    main()

# TODO: Weitere Funktionen und Logik des Skripts (Git Commands) hinzufügen