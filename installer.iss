; Inno Setup Compiler Script (5.x or 6.x)
; Creates Windows Installer "NaughtyAI_Setup.exe"

#define MyAppName "Naughty AI Assistant"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Naughty AI Labs"
#define MyAppURL "https://github.com/moonrox420/Naughty-AI-Assistant"
#define MyAppExeName "NaughtyAI.exe"

[Setup]
AppId={{D8A1397F-2C94-4F91-884A-913076F4E85C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\NaughtyAIAssistant
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist\installer
OutputBaseFilename=NaughtyAI_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Standalone compiled executable
Source: "dist\NaughtyAI.exe"; DestDir: "{app}"; Flags: ignoreversion
; Web static assets and resources
Source: "static\*"; DestDir: "{app}\static"; Flags: ignoreversion recursesubdirs createallsubdirs
; Scripts and documentation
Source: "start_app.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "start_all.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Launch Assistant + SD Forge"; Filename: "{app}\start_all.bat"; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
