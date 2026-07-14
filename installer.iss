; Inno Setup script - builds a standard Windows installer:
; installs to Program Files, adds Start Menu + optional desktop shortcut,
; optional "start with Windows", and a normal uninstaller.
; Compile with Inno Setup (https://jrsoftware.org/isinfo.php) after
; building dist\EchoQuill.exe with build_exe.bat.

#define AppName "EchoQuill"
#define AppVersion "1.17.3"
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
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; upgrades install over the old version silently - no manual uninstall
CloseApplications=force
RestartApplications=no
AppMutex=EchoQuill_SingleInstance

[Files]
Source: "dist\EchoQuill\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
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

[InstallDelete]
; stale shortcuts from older versions
Type: files; Name: "{autodesktop}\EchoQuill.lnk"
; leftover single-file exe from pre-1.13.2 layouts
Type: files; Name: "{app}\EchoQuill.exe"

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch EchoQuill now"; Flags: nowait postinstall skipifsilent
Filename: "{app}\{#AppExe}"; Flags: nowait; Check: WizardSilent

[UninstallRun]
Filename: "taskkill.exe"; Parameters: "/F /IM EchoQuill.exe"; Flags: runhidden; RunOnceId: "KillEchoQuill"

[Code]
var ResultCode: Integer;

procedure SweepTempPattern(const Pattern: string);
var
  FindRec: TFindRec;
  TempDir: string;
begin
  TempDir := ExpandConstant('{localappdata}') + '\Temp';
  if FindFirst(TempDir + '\' + Pattern, FindRec) then begin
    try
      repeat
        if FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY <> 0 then
          DelTree(TempDir + '\' + FindRec.Name, True, True, True);
      until not FindNext(FindRec);
    finally
      FindClose(FindRec);
    end;
  end;
end;

procedure CleanOldTempUnpacks();
begin
  SweepTempPattern('_MEI*');        { old single-file unpacks }
  SweepTempPattern('echoquill_*');  { leftover downloaded audio }
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then begin
    { refresh the Windows icon cache so the new version badge shows }
    Exec('ie4uinit.exe', '-show', '', SW_HIDE, ewNoWait, ResultCode);
  end;
  if CurStep = ssInstall then begin
    { make sure no copy is running, old or new }
    Exec('taskkill.exe', '/F /IM EchoQuill.exe', '', SW_HIDE,
         ewWaitUntilTerminated, ResultCode);
    CleanOldTempUnpacks();
    { clear stale auto-start entries pointing at dead locations;
      the app rewrites the correct one on launch if enabled }
    RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run',
                   'EchoQuill');
  end;
end;
