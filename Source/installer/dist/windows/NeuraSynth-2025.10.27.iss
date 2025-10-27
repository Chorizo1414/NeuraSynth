[Setup]
AppId={{NeuraSynth}}
AppName=NeuraSynth
AppVersion=2025.10.27
AppPublisher=NeuraSynth
DefaultDirName={{userdocs}}\NeuraSynth
DefaultGroupName=NeuraSynth
OutputBaseFilename=NeuraSynth-2025.10.27-Setup
ArchitecturesInstallIn64BitMode=x64
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes
DisableDirPage=yes
DisableWelcomePage=no
; LicenseFile=<ruta_a_la_licencia>
WizardSmallImageFile="C:\\Users\\Progra.CHORI1414\\Desktop\\Proyectos\\JUCE\\NeuraSynth\\Source\\installer\\dist\\staging\\NeuraSynth-2025.10.27-windows\\branding\\icon.png"
SetupIconFile="C:\\Users\\Progra.CHORI1414\\Desktop\\Proyectos\\JUCE\\NeuraSynth\\Source\\installer\\dist\\staging\\NeuraSynth-2025.10.27-windows\\branding\\icon.ico"
UninstallDisplayIcon={app}\branding\icon.ico
[Components]
Name: "standalone"; Description: "Aplicación standalone"; Types: full
Name: "vst3"; Description: "Plugin VST3"; Types: full
[Files]
Source: "C:/Users/Progra.CHORI1414/Desktop/Proyectos/JUCE/NeuraSynth/Source/installer/dist/staging/NeuraSynth-2025.10.27-windows/Standalone\\*"; DestDir: "{app}"; Components: standalone; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:/Users/Progra.CHORI1414/Desktop/Proyectos/JUCE/NeuraSynth/Source/installer/dist/staging/NeuraSynth-2025.10.27-windows/VST3\\*"; DestDir: "{code:GetVst3Dir}"; Components: vst3; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:/Users/Progra.CHORI1414/Desktop/Proyectos/JUCE/NeuraSynth/Source/installer/dist/staging/NeuraSynth-2025.10.27-windows/branding\\*"; DestDir: "{app}\branding"; Components: standalone; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:/Users/Progra.CHORI1414/Desktop/Proyectos/JUCE/NeuraSynth/Source/installer/dist/staging/NeuraSynth-2025.10.27-windows/Python\\*"; DestDir: "{app}\Python"; Components: standalone; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\\NeuraSynth"; Filename: "{app}\\NeuraSynth.exe"; Components: standalone; IconFilename: "{app}\\branding\\icon.ico"
Name: "{autodesktop}\\NeuraSynth"; Filename: "{app}\\NeuraSynth.exe"; Components: standalone; IconFilename: "{app}\\branding\\icon.ico"
[Run]
Filename: "{app}\NeuraSynth.exe"; Description: "Iniciar NeuraSynth"; Components: standalone; Flags: nowait postinstall skipifsilent

[Code]
const
  StandaloneFileName = 'NeuraSynth.exe';
  Vst3ItemName = 'NeuraSynth.vst3';

var
  InstallDirsPage: TInputDirWizardPage;
  PrevStandaloneDir: string;
  ExistingStandaloneDir: string;
  Vst3DirValue: string;

function PreviousInstallExists(): Boolean;
var
  existingStandalone: string;
  existingVst3: string;
begin
  Result := RegKeyExists(HKLM, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{NeuraSynth}_is1') or RegKeyExists(HKCU, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{NeuraSynth}_is1');
  if Result then begin
    if not RegQueryStringValue(HKLM, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{NeuraSynth}_is1', 'InstallLocation', PrevStandaloneDir) then
      RegQueryStringValue(HKCU, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{NeuraSynth}_is1', 'InstallLocation', PrevStandaloneDir);
  end;

  ExistingStandaloneDir := PrevStandaloneDir;
  if ExistingStandaloneDir = '' then
    ExistingStandaloneDir := ExpandConstant('{userdocs}\NeuraSynth');
  ExistingStandaloneDir := RemoveBackslashUnlessRoot(ExistingStandaloneDir);
  existingStandalone := AddBackslash(ExistingStandaloneDir) + StandaloneFileName;
  existingVst3 := ExpandConstant('{commoncf64}\VST3\') + Vst3ItemName;
  if not Result then
    Result := FileExists(existingStandalone) or DirExists(existingStandalone);
  if not Result then
    Result := FileExists(existingVst3) or DirExists(existingVst3);
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  if PreviousInstallExists() then
  begin
    if MsgBox('Se detectó una instalación previa de NeuraSynth. ¿Deseas reemplazarla?', mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDNO then
      Result := False;
  end;
end;

procedure InitializeWizard;
begin
  if PrevStandaloneDir = '' then
  begin
    PrevStandaloneDir := ExpandConstant('{userdocs}\NeuraSynth');
  end
  else
  begin
    PrevStandaloneDir := RemoveBackslashUnlessRoot(PrevStandaloneDir);
  end;
  Vst3DirValue := ExpandConstant('{commoncf64}\VST3');
  InstallDirsPage := CreateInputDirPage(wpSelectComponents,
    'Carpetas de instalación',
    'Selecciona dónde instalar NeuraSynth',
    'Elige las rutas de instalación para cada componente. Puedes cambiar la carpeta del modo standalone. El plugin VST3 se instalará en la ubicación estándar de tu sistema.',
    False, '');
  InstallDirsPage.Add('Standalone');
  InstallDirsPage.Values[0] := PrevStandaloneDir;
  WizardForm.DirEdit.Text := InstallDirsPage.Values[0];
  InstallDirsPage.Add('VST3 (solo lectura)');
  InstallDirsPage.Values[1] := Vst3DirValue;
  InstallDirsPage.Edits[1].Enabled := False;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = InstallDirsPage.ID then
  begin
    if InstallDirsPage.Values[0] = '' then
    begin
      MsgBox('Selecciona una carpeta válida para la aplicación standalone.', mbError, MB_OK);
      Result := False;
    end
    else
      WizardForm.DirEdit.Text := InstallDirsPage.Values[0];
  end;
end;

function GetVst3Dir(Param: string): string;
begin
  Result := Vst3DirValue;
end;
