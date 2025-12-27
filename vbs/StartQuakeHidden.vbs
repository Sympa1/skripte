  Set WshShell = CreateObject("WScript.Shell")
  ' Die 0 am Ende steht für "Fenster verstecken"
  WshShell.Run "wt -w _quake", 0, False