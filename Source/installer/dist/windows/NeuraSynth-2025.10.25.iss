[Setup]
AppId={{NeuraSynth}}
AppName=NeuraSynth
AppVersion=2025.10.25
AppPublisher=NeuraSynth
DefaultDirName={{pf64}}\NeuraSynth\NeuraSynth
DefaultGroupName=NeuraSynth
OutputBaseFilename=NeuraSynth-2025.10.25-Setup
ArchitecturesInstallIn64BitMode=x64
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes
; LicenseFile=<ruta_a_la_licencia>
WizardSmallImageFile=C:\Users\Progra.CHORI1414\Desktop\Proyectos\JUCE\NeuraSynth\Source\installer\dist\staging\NeuraSynth-2025.10.25-windows\branding\icon.png
[Files]
Source: "C:/Users/Progra.CHORI1414/Desktop/Proyectos/JUCE/NeuraSynth/Source/installer/dist/staging/NeuraSynth-2025.10.25-windows/Standalone\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:/Users/Progra.CHORI1414/Desktop/Proyectos/JUCE/NeuraSynth/Source/installer/dist/staging/NeuraSynth-2025.10.25-windows/VST3\*"; DestDir: "{commoncf64}\VST3"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\NeuraSynth"; Filename: "{app}\NeuraSynth.exe"

[Run]
Filename: "{app}\NeuraSynth.exe"; Description: "Iniciar NeuraSynth"; Flags: nowait postinstall skipifsilent
