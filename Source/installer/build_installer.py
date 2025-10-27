#!/usr/bin/env python3
"""Utility helpers to assemble redistributable NeuraSynth installers.

The script collects the standalone executable, the VST3 bundle and optional
runtime assets into a staging directory and optionally creates distributable
archives or Windows Inno Setup scripts.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional


SCRIPT_ROOT = Path(__file__).resolve().parent


def _detect_repo_root(start: Path) -> Path:
    markers = {".git", "NeuraSynth.jucer"}

    for current in [start] + list(start.parents):
        if any((current / marker).exists() for marker in markers):
            return current

    return start


REPO_ROOT = _detect_repo_root(SCRIPT_ROOT)
DEFAULT_LOGO = SCRIPT_ROOT / "resources" / "icon.png"
DEFAULT_PYTHON_RUNTIME_ROOT = SCRIPT_ROOT / "python-runtime"
NEURACHORD_SOURCE = REPO_ROOT / "Source" / "NeuraChord"


def _parse_png_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("El archivo proporcionado no es un PNG válido.")

    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    return width, height


def _ensure_ico_for_png(png_path: Path) -> Path:
    data = png_path.read_bytes()
    width, height = _parse_png_dimensions(data)

    if width > 256 or height > 256:
        raise ValueError(
            "El PNG excede las dimensiones admitidas para un icono (256x256)."
        )
    
    entry = bytearray()
    entry += (0 if width == 256 else width).to_bytes(1, "little")
    entry += (0 if height == 256 else height).to_bytes(1, "little")
    entry += (0).to_bytes(1, "little")  # colour count
    entry += (0).to_bytes(1, "little")  # reserved
    entry += (0).to_bytes(2, "little")  # planes (0 when data is PNG)
    entry += (0).to_bytes(2, "little")  # bit count (0 when data is PNG)
    entry += len(data).to_bytes(4, "little")
    entry += (6 + 16).to_bytes(4, "little")  # offset after header + entry

    ico_bytes = bytearray()
    ico_bytes += (0).to_bytes(2, "little")
    ico_bytes += (1).to_bytes(2, "little")
    ico_bytes += (1).to_bytes(2, "little")
    ico_bytes += entry
    ico_bytes += data

    ico_path = png_path.with_suffix(".ico")
    ico_path.write_bytes(ico_bytes)
    return ico_path


def _collect_default_python_payloads(platform_key: str) -> list[Path]:
    payloads: list[Path] = []

    runtime_root = DEFAULT_PYTHON_RUNTIME_ROOT / platform_key
    if runtime_root.exists():
        for child in runtime_root.iterdir():
            if child.name.startswith("."):
                continue
            payloads.append(child)

    if NEURACHORD_SOURCE.exists():
        payloads.append(NEURACHORD_SOURCE)

    return payloads


def _format_inno_path(path: Path) -> str:
    return str(path).replace("\\", "\\\\")


def _normalise_platform(value: Optional[str]) -> str:
    if value is None:
        current = sys.platform
    else:
        current = value.lower()

    if current.startswith("win"):
        return "windows"
    if current.startswith("darwin") or current in {"mac", "macos"}:
        return "macos"
    if current.startswith("linux"):
        return "linux"

    raise ValueError(f"Unsupported platform '{value}'. Expected windows/macos/linux.")


def _copy_any(src: Path, dest: Path) -> None:
    if src.is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def _score_candidate(path: Path, *, keywords: tuple[str, ...] = ()) -> tuple[int, float]:
    parts_lower = [part.lower() for part in path.parts]
    score = 0

    if "release" in parts_lower:
        score += 5
    if "x64" in parts_lower or "arm64" in parts_lower:
        score += 2
    if "build" in parts_lower or "builds" in parts_lower:
        score += 1

    for keyword in keywords:
        if any(keyword in part for part in parts_lower):
            score += 3

    try:
        mtime = path.stat().st_mtime
    except FileNotFoundError:
        mtime = 0.0

    return score, mtime


def _autodetect_artifact(product_name: str, platform_key: str, kind: str) -> Optional[Path]:
    product_base = product_name.replace(" ", "")

    if kind == "standalone":
        if platform_key == "windows":
            patterns = [f"{product_base}.exe", f"{product_name}.exe"]
        elif platform_key == "macos":
            patterns = [f"{product_base}.app", f"{product_name}.app"]
        else:
            patterns = [product_base, product_name]
        keywords = ("standalone", "standaloneplugin", "app")
    else:  # vst3
        patterns = [f"{product_base}.vst3", f"{product_name}.vst3"]
        keywords = ("vst3",)

    candidates: set[Path] = set()
    for pattern in patterns:
        for path in REPO_ROOT.rglob(pattern):
            if path.is_file() or path.is_dir():
                candidates.add(path)

    if not candidates:
        return None

    best = max(candidates, key=lambda p: _score_candidate(p, keywords=keywords))
    return best


def _autodetect_version() -> Optional[str]:
    git_dir = REPO_ROOT

    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=False,
            cwd=git_dir,
        )
        if result.returncode == 0:
            candidate = result.stdout.strip()
            if candidate:
                return candidate
    except FileNotFoundError:
        pass

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            cwd=git_dir,
        )
        if result.returncode == 0:
            candidate = result.stdout.strip()
            if candidate:
                return candidate
    except FileNotFoundError:
        pass

    return datetime.utcnow().strftime("%Y.%m.%d")


def _write_install_instructions(target: Path, platform_key: str, product_name: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)

    common = [
        "# NeuraSynth",
        "",
        f"Este paquete contiene los binarios de {product_name} y sus dependencias básicas.",
        "",
        "## Contenido",
        "- `Standalone/`: aplicación autónoma (ejecutable o paquete).",
        "- `VST3/`: plugin VST3 listo para copiarse en la carpeta estándar del sistema.",
    ]

    if platform_key == "windows":
        instructions = [
            "",
            "## Instalación en Windows",
            "1. Ejecuta `Setup.exe` si está disponible o copia manualmente los archivos:",
            "   - Copia la carpeta `Standalone` a `C\\\Program Files\\NeuraSynth` (o la ruta que prefieras).",
            "   - Copia `VST3/NeuraSynth.vst3` a `C\\\Program Files\\Common Files\\VST3`.",
            "2. Inicia tu DAW y reescanea la carpeta de plugins.",
        ]
    elif platform_key == "macos":
        instructions = [
            "",
            "## Instalación en macOS",
            "1. Copia `Standalone/NeuraSynth.app` a `/Applications/NeuraSynth`.",
            "2. Copia `VST3/NeuraSynth.vst3` a `~/Library/Audio/Plug-Ins/VST3` (o `/Library/Audio/Plug-Ins/VST3` para todos los usuarios).",
            "3. Abre el plugin desde tu DAW y permite su ejecución en Preferencias del Sistema si macOS lo solicita.",
        ]
    else:  # linux
        instructions = [
            "",
            "## Instalación en Linux",
            "1. Copia el binario standalone a `/opt/NeuraSynth` y crea un lanzador si lo deseas.",
            "2. Copia `VST3/NeuraSynth.vst3` a `~/.vst3` o `/usr/lib/vst3` según tus permisos.",
            "3. Asegúrate de exportar `PYTHONHOME` y `PYTHONPATH` si vas a usar la integración NeuraChord.",
        ]

    content = "\n".join(common + instructions)
    target.write_text(content, encoding="utf-8")


def _write_metadata(target: Path, *, version: str, platform_key: str, standalone: Path, vst3: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "product": "NeuraSynth",
        "version": version,
        "platform": platform_key,
        "created": datetime.utcnow().isoformat() + "Z",
        "standalone": standalone.name,
        "vst3": vst3.name,
    }
    target.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _generate_inno_script(output_dir: Path, *, product_name: str, version: str, company: str,
                          staging_root: Path, wizard_logo: Optional[Path], shortcut_icon: Optional[Path],
                          license_file: Optional[Path]) -> Path:
    script_path = output_dir / f"{product_name.replace(' ', '')}-{version}.iss"
    output_dir.mkdir(parents=True, exist_ok=True)

    wizard_small_image = (
        f"WizardSmallImageFile=\"{_format_inno_path(wizard_logo)}\""
        if wizard_logo else "; WizardSmallImageFile=<ruta_al_logo>"
    )
    license_entry = (
        f"LicenseFile=\"{_format_inno_path(license_file)}\""
        if license_file else "; LicenseFile=<ruta_a_la_licencia>"
    )
    setup_icon = (
        f"SetupIconFile=\"{_format_inno_path(shortcut_icon)}\""
        if shortcut_icon else "; SetupIconFile=<ruta_al_icono>"
    )
    uninstall_icon = (
        f"UninstallDisplayIcon={{app}}\\branding\\{shortcut_icon.name}"
        if shortcut_icon else "; UninstallDisplayIcon=<ruta_al_icono>"
    )

    setup_section = (
        f"[Setup]\n"
        f"AppId={{{{{product_name.replace(' ', '')}}}}}\n"
        f"AppName={product_name}\n"
        f"AppVersion={version}\n"
        f"AppPublisher={company}\n"
        f"DefaultDirName={{{{userdocs}}}}\\{product_name}\n"
        f"DefaultGroupName={product_name}\n"
        f"OutputBaseFilename={product_name.replace(' ', '')}-{version}-Setup\n"
        "ArchitecturesInstallIn64BitMode=x64\n"
        "Compression=lzma\n"
        "SolidCompression=yes\n"
        "DisableProgramGroupPage=yes\n"
        "DisableDirPage=yes\n"
        "DisableWelcomePage=no\n"
        f"{license_entry}\n"
        f"{wizard_small_image}\n"
        f"{setup_icon}\n"
        f"{uninstall_icon}"
    )

    files_lines = [
        f"Source: \"{(staging_root / 'Standalone').as_posix()}\\\\*\"; DestDir: \"{{app}}\"; Components: standalone; Flags: ignoreversion recursesubdirs createallsubdirs",
        f"Source: \"{(staging_root / 'VST3').as_posix()}\\\\*\"; DestDir: \"{{code:GetVst3Dir}}\"; Components: vst3; Flags: ignoreversion recursesubdirs createallsubdirs",
    ]

    optional_dirs = [
        ("branding", "{app}\\branding"),
        ("Resources", "{app}\\Resources"),
        ("Python", "{app}\\Python"),
    ]

    for folder, destination in optional_dirs:
        folder_path = staging_root / folder
        if folder_path.exists():
            files_lines.append(
                f"Source: \"{folder_path.as_posix()}\\\\*\"; DestDir: \"{destination}\"; Components: standalone; Flags: ignoreversion recursesubdirs createallsubdirs"
            )

    files_section = "[Files]\n" + "\n".join(files_lines)

    standalone_entries = list((staging_root / "Standalone").iterdir())
    standalone_target = standalone_entries[0].name if standalone_entries else "NeuraSynth.exe"
    vst3_entries = list((staging_root / "VST3").iterdir())
    vst3_target = vst3_entries[0].name if vst3_entries else "NeuraSynth.vst3"

    icon_filename_clause = (
        f"; IconFilename: \"{{app}}\\\\branding\\\\{shortcut_icon.name}\""
        if shortcut_icon else ""
    )

    icons_section = (
        "[Icons]\n"
        f"Name: \"{{group}}\\\\{product_name}\"; Filename: \"{{app}}\\\\{standalone_target}\"; Components: standalone{icon_filename_clause}\n"
        f"Name: \"{{autodesktop}}\\\\{product_name}\"; Filename: \"{{app}}\\\\{standalone_target}\"; Components: standalone{icon_filename_clause}"
    )

    run_section = f"""[Run]
Filename: "{{app}}\\{standalone_target}"; Description: "Iniciar {product_name}"; Components: standalone; Flags: nowait postinstall skipifsilent
"""

    components_section = (
        "[Components]\n"
        "Name: \"standalone\"; Description: \"Aplicación standalone\"; Types: full\n"
        "Name: \"vst3\"; Description: \"Plugin VST3\"; Types: full"
    )

    app_id_literal = f"{{{product_name.replace(' ', '')}}}"
    uninstall_key = f"Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\{app_id_literal}_is1"
    standalone_default_dir = "{userdocs}\\" + product_name
    vst3_default_dir = "{commoncf64}\\VST3"

    code_section = f"""[Code]
const
  StandaloneFileName = '{standalone_target}';
  Vst3ItemName = '{vst3_target}';

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
  Result := RegKeyExists(HKLM, '{uninstall_key}') or RegKeyExists(HKCU, '{uninstall_key}');
  if Result then begin
    if not RegQueryStringValue(HKLM, '{uninstall_key}', 'InstallLocation', PrevStandaloneDir) then
      RegQueryStringValue(HKCU, '{uninstall_key}', 'InstallLocation', PrevStandaloneDir);
  end;

  ExistingStandaloneDir := PrevStandaloneDir;
  if ExistingStandaloneDir = '' then
    ExistingStandaloneDir := ExpandConstant('{standalone_default_dir}');
  ExistingStandaloneDir := RemoveBackslashUnlessRoot(ExistingStandaloneDir);
  existingStandalone := AddBackslash(ExistingStandaloneDir) + StandaloneFileName;
  existingVst3 := ExpandConstant('{vst3_default_dir}\\') + Vst3ItemName;
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
    if MsgBox('Se detectó una instalación previa de {product_name}. ¿Deseas reemplazarla?', mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDNO then
      Result := False;
  end;
end;

procedure InitializeWizard;
begin
  if PrevStandaloneDir = '' then
  begin
    PrevStandaloneDir := ExpandConstant('{standalone_default_dir}');
  end
  else
  begin
    PrevStandaloneDir := RemoveBackslashUnlessRoot(PrevStandaloneDir);
  end;
  Vst3DirValue := ExpandConstant('{vst3_default_dir}');
  InstallDirsPage := CreateInputDirPage(wpSelectComponents,
    'Carpetas de instalación',
    'Selecciona dónde instalar {product_name}',
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
"""

    script_content = (
        setup_section
        + "\n"
        + components_section
        + "\n"
        + files_section
        + "\n"
        + icons_section
        + "\n"
        + run_section
        + "\n"
        + code_section
    )

    script_path.write_text(script_content, encoding="utf-8")
    return script_path


def _create_archives(platform_key: str, staging_root: Path, output_dir: Path, product_name: str, version: str) -> list[Path]:
    archives: list[Path] = []
    archive_base = output_dir / f"{product_name.replace(' ', '')}-{version}-{platform_key}"

    output_dir.mkdir(parents=True, exist_ok=True)

    root_dir = staging_root.parent
    base_dir = staging_root.name

    if platform_key == "windows":
        archive = shutil.make_archive(str(archive_base), "zip", root_dir=root_dir, base_dir=base_dir)
        archives.append(Path(archive))
    else:
        archive = shutil.make_archive(str(archive_base), "gztar", root_dir=root_dir, base_dir=base_dir)
        archives.append(Path(archive))

    return archives


def build_installer(args: argparse.Namespace) -> None:
    platform_key = _normalise_platform(args.platform)

    version = args.version
    if not version:
        version = _autodetect_version()
        print(f"[INFO] Versión detectada automáticamente: {version}")

    if args.standalone:
        standalone = Path(args.standalone).expanduser().resolve()
    else:
        standalone = _autodetect_artifact(args.product_name, platform_key, "standalone")
        if standalone:
            standalone = standalone.resolve()
            print(f"[INFO] Standalone detectado automáticamente en: {standalone}")
    if standalone is None:
        raise FileNotFoundError(
            "No se encontró el binario standalone. Compila el proyecto o proporciona --standalone."
        )

    if args.vst3:
        vst3 = Path(args.vst3).expanduser().resolve()
    else:
        vst3 = _autodetect_artifact(args.product_name, platform_key, "vst3")
        if vst3:
            vst3 = vst3.resolve()
            print(f"[INFO] VST3 detectado automáticamente en: {vst3}")
    if vst3 is None:
        raise FileNotFoundError(
            "No se encontró el plugin VST3. Compila el proyecto o proporciona --vst3."
        )

    if not standalone.exists():
        raise FileNotFoundError(f"Standalone binary '{standalone}' no existe.")
    if not vst3.exists():
        raise FileNotFoundError(f"Plugin VST3 '{vst3}' no existe.")

    output_dir = Path(args.output).expanduser().resolve()
    staging_root = output_dir / "staging" / f"{args.product_name.replace(' ', '')}-{version}-{platform_key}"

    if staging_root.exists():
        shutil.rmtree(staging_root)

    standalone_dest = staging_root / "Standalone" / standalone.name
    vst3_dest = staging_root / "VST3" / vst3.name

    _copy_any(standalone, standalone_dest)
    _copy_any(vst3, vst3_dest)

    for resource in args.resources:
        resource_path = Path(resource).expanduser().resolve()
        if not resource_path.exists():
            raise FileNotFoundError(f"Recurso adicional '{resource_path}' no existe.")
        dest = staging_root / "Resources" / resource_path.name
        _copy_any(resource_path, dest)

    python_payloads: list[Path] = []
    seen_payloads: set[Path] = set()

    def _add_python_payload(path: Path) -> None:
        resolved = path.resolve()
        if resolved in seen_payloads:
            return
        seen_payloads.add(resolved)
        python_payloads.append(resolved)

    for runtime in args.python_runtime:
        runtime_path = Path(runtime).expanduser().resolve()
        if not runtime_path.exists():
            raise FileNotFoundError(f"Ruta de Python '{runtime_path}' no existe.")
        _add_python_payload(runtime_path)

    defaults = _collect_default_python_payloads(platform_key)
    for default in defaults:
        if default.exists():
            _add_python_payload(default)

    if not args.python_runtime and defaults:
        pretty_defaults = ", ".join(str(path) for path in defaults if path.exists())
        if pretty_defaults:
            print(f"[INFO] Recursos de Python detectados automáticamente: {pretty_defaults}")
    elif not python_payloads:
        print("[ADVERTENCIA] No se especificaron rutas de Python. El ejecutable requerirá un intérprete externo.")

    for payload in python_payloads:
        dest = staging_root / "Python" / payload.name
        _copy_any(payload, dest)

    python_root = staging_root / "Python"
    if python_root.exists():
        has_embedded_runtime = (
            any(python_root.rglob("python3*.dll"))
            or any(python_root.rglob("libpython3*.so"))
            or any(python_root.rglob("libpython3*.dylib"))
        )
        if not has_embedded_runtime:
            print("[ADVERTENCIA] La carpeta Python no contiene un runtime embebido (python3*.dll). Comprueba que copiaste la distribución embebida de Python.")
        else:
            standalone_dir = staging_root / "Standalone"
            standalone_dir.mkdir(parents=True, exist_ok=True)

            dll_sources: dict[str, Path] = {}
            for dll in python_root.rglob("python3*.dll"):
                if dll.is_file():
                    dll_sources.setdefault(dll.name, dll)

            for name, source in dll_sources.items():
                target = standalone_dir / name
                shutil.copy2(source, target)

    install_md = staging_root / "INSTALL.md"
    _write_install_instructions(install_md, platform_key, args.product_name)

    metadata_path = staging_root / "metadata.json"
    _write_metadata(metadata_path, version=version, platform_key=platform_key,
                    standalone=standalone, vst3=vst3)

    wizard_logo: Optional[Path] = None
    shortcut_icon: Optional[Path] = None
    logo_candidate: Optional[Path]
    if args.logo:
        logo_candidate = Path(args.logo).expanduser().resolve()
        if not logo_candidate.exists():
            raise FileNotFoundError(f"Logo '{logo_candidate}' no existe.")
    else:
        logo_candidate = DEFAULT_LOGO if DEFAULT_LOGO.exists() else None

    if logo_candidate is not None:
        staging_logo = staging_root / "branding" / logo_candidate.name
        _copy_any(logo_candidate, staging_logo)

        suffix = staging_logo.suffix.lower()
        if suffix == ".png":
            wizard_logo = staging_logo
            try:
                shortcut_icon = _ensure_ico_for_png(staging_logo)
            except ValueError as exc:
                print(f"[ADVERTENCIA] No se pudo convertir el logo a ICO: {exc}")
        elif suffix == ".ico":
            shortcut_icon = staging_logo
        elif suffix in {".bmp", ".jpg", ".jpeg"}:
            wizard_logo = staging_logo
        else:
            print(f"[ADVERTENCIA] Formato de logo '{suffix}' no reconocido. Se omitirá en el instalador.")
    else:
        print("[INFO] No se incluyó logotipo porque no se encontró ninguno en installer/resources ni se proporcionó --logo.")

    license_for_script: Optional[Path] = None
    if args.license:
        license_path = Path(args.license).expanduser().resolve()
        if not license_path.exists():
            raise FileNotFoundError(f"Licencia '{license_path}' no existe.")
        license_for_script = license_path

    archives = []
    if not args.skip_archive:
        archives = _create_archives(platform_key, staging_root, output_dir, args.product_name, version)

    inno_script = None
    if platform_key == "windows":
        inno_output = output_dir / "windows"
        inno_script = _generate_inno_script(inno_output, product_name=args.product_name, version=version,
                                            company=args.company_name, staging_root=staging_root,
                                            wizard_logo=wizard_logo, shortcut_icon=shortcut_icon,
                                            license_file=license_for_script)
        if not args.only_generate_scripts:
            iscc = shutil.which("iscc")
            if iscc:
                try:
                    subprocess.run([iscc, str(inno_script)], check=True)
                except subprocess.CalledProcessError as exc:
                    print(f"[ADVERTENCIA] No se pudo compilar el instalador con Inno Setup: {exc}", file=sys.stderr)
            else:
                print("[INFO] Inno Setup no está disponible en PATH. Se generó el script .iss para compilar manualmente.")

    summary = {
        "staging_root": str(staging_root),
        "archives": [str(p) for p in archives],
        "inno_script": str(inno_script) if inno_script else None,
        "version": version,
    }
    print(json.dumps(summary, indent=2))


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Empaqueta los binarios de NeuraSynth en un instalador redistribuible.")
    parser.add_argument("--standalone", help="Ruta al binario standalone compilado (se detecta automáticamente si es posible).")
    parser.add_argument("--vst3", help="Ruta al bundle o archivo VST3 (se detecta automáticamente si es posible).")
    parser.add_argument("--version", help="Versión del producto (se detecta desde git si se omite).")
    parser.add_argument("--output", default="dist", help="Carpeta de salida para staging y artefactos.")
    parser.add_argument("--platform", choices=["windows", "macos", "linux"], help="Plataforma destino.")
    parser.add_argument("--company-name", default="NeuraSynth", help="Nombre de la compañía para el instalador.")
    parser.add_argument("--product-name", default="NeuraSynth", help="Nombre del producto mostrado al usuario.")
    parser.add_argument("--license", help="Ruta al archivo de licencia para el instalador (opcional).")
    parser.add_argument("--logo", help="Logo opcional para branding del instalador. Por defecto usa installer/resources/icon.png si existe.")
    parser.add_argument("--python-runtime", action="append", default=[],
                        help="Rutas adicionales de Python a incluir en el paquete (se puede repetir).")
    parser.add_argument("--resources", action="append", default=[],
                        help="Recursos adicionales (presets, documentación, etc.).")
    parser.add_argument("--skip-archive", action="store_true", help="No generar archivos comprimidos finales.")
    parser.add_argument("--only-generate-scripts", action="store_true",
                        help="Genera únicamente el script de Inno Setup si corresponde.")

    return parser.parse_args(argv)


if __name__ == "__main__":
    build_installer(parse_args())