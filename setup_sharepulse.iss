[Setup]
AppName=SharePulse
AppVersion=1.0
DefaultDirName={commonpf}\SharePulse
PrivilegesRequired=admin
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=SharePulseInstaller
SetupIconFile=sharepulse.ico
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "SharePulse.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "sharepulse.ico"; DestDir: "{app}"; Flags: ignoreversion

[Run]
; Launch SharePulse immediately after install (if not silent)
Filename: "{app}\\SharePulse.exe"; \
  Flags: nowait postinstall skipifsilent

[Icons]
; Startup shortcut for all users
Name: "{commonstartup}\\SharePulse"; \
  Filename: "{app}\\SharePulse.exe"; \
  WorkingDir: "{app}"; \
  IconFilename: "{app}\\sharepulse.ico"; \
  IconIndex: 0
