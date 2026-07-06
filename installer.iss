; Inno Setup script - builds a standard Windows installer:
; installs to Program Files, adds Start Menu + optional desktop shortcut,
; optional "start with Windows", and a normal uninstaller.
; Compile with Inno Setup (https://jrsoftware.org/isinfo.php) after
; building dist\EchoQuill.exe with build_exe.bat.

#define AppName "EchoQuill"
#define AppVersion "1.13.1"
#define AppExe "EchoQuill.exe"

[Setup]
AppId={{7F3C1B2A-6D24-4E8B-9C11-3A5E8F1D2B4C}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=EchoQuill contributors
DefaultDirName={autopf}\EchoQuill
DefaultGroupName=EchoQuill
UninstallDisplayIcon={app}\{#AppExe}
OutputBaseFilename=EchoQuill-Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequiredOverridesAllowed=dialog

[Files]
Source: "dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\EchoQuill"; Filename: "{app}\{#AppExe}"; Comment: "EchoQuill v{#AppVersion} - free local voice dictation"
Name: "{group}\Uninstall EchoQuill"; Filename: "{uninstallexe}"
Name: "{autodesktop}\EchoQuill"; Filename: "{app}\{#AppExe}"; Comment: "EchoQuill v{#AppVersion} - free local voice dictation"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "startup"; Description: "Start EchoQuill automatically with &Windows"; GroupDescription: "Startup:"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "EchoQuill"; ValueData: """{app}\{#AppExe}"""; \
  Flags: uninsdeletevalue; Tasks: startup

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch EchoQuill now"; Flags: nowait postinstall skipifsilent
