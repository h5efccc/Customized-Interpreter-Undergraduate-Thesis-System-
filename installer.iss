; PNC Simulator Inno Setup Script
; Production-grade Windows Application Installer

[Setup]
AppId={{C7A9E5B2-D4A1-4F9E-8B6C-123456789ABC}
AppName=PNC Simulator
AppVersion=1.0
AppPublisher=PNC Language Team
AppPublisherURL=https://github.com/h5efccc/Customized-Interpreter-Undergraduate-Thesis-System-
AppSupportURL=https://github.com/h5efccc/Customized-Interpreter-Undergraduate-Thesis-System-
AppUpdatesURL=https://github.com/h5efccc/Customized-Interpreter-Undergraduate-Thesis-System-
DefaultDirName={autopf}\PNC_Simulator
DefaultGroupName=PNC Simulator
AllowNoIcons=yes
; Save the installer in the project root
OutputDir=.
OutputBaseFilename=PNC_Simulator_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Source is the 'dist\edu_interpreter' folder from PyInstaller multi-file build
Source: "dist\edu_interpreter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\PNC Simulator"; Filename: "{app}\edu_interpreter.exe"
Name: "{autodesktop}\PNC Simulator"; Filename: "{app}\edu_interpreter.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\edu_interpreter.exe"; Description: "{cm:LaunchProgram,PNC Simulator}"; Flags: nowait postinstall
