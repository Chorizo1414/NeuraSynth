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
DEFAULT_LOGO = SCRIPT_ROOT / "resources" / "icon.png"


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
                          staging_root: Path, logo: Optional[Path], license_file: Optional[Path]) -> Path:
    script_path = output_dir / f"{product_name.replace(' ', '')}-{version}.iss"
    output_dir.mkdir(parents=True, exist_ok=True)

    wizard_small_image = f"WizardSmallImageFile={logo}" if logo else "; WizardSmallImageFile=<ruta_al_logo>"
    license_entry = f"LicenseFile={license_file}" if license_file else "; LicenseFile=<ruta_a_la_licencia>"

    setup_section = f"""[Setup]
AppId={{{{{{product_name.replace(' ', '')}}}}}}
AppName={product_name}
AppVersion={version}
AppPublisher={company}
DefaultDirName={{{pf64}}}\{company}\{product_name}
DefaultGroupName={product_name}
OutputBaseFilename={product_name.replace(' ', '')}-{version}-Setup
ArchitecturesInstallIn64BitMode=x64
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes
{license_entry}
{wizard_small_image}
"""

    files_section = f"""[Files]
Source: "{(staging_root / 'Standalone').as_posix()}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{(staging_root / 'VST3').as_posix()}\\*"; DestDir: "{{commoncf64}}\\VST3"; Flags: ignoreversion recursesubdirs createallsubdirs
"""

    standalone_entries = list((staging_root / "Standalone").iterdir())
    standalone_target = standalone_entries[0].name if standalone_entries else "NeuraSynth.exe"

    icons_section = f"""[Icons]
Name: "{{group}}\\{product_name}"; Filename: "{{app}}\\{standalone_target}"
"""

    run_section = f"""[Run]
Filename: "{{app}}\\{standalone_target}"; Description: "Iniciar {product_name}"; Flags: nowait postinstall skipifsilent
"""

    script_path.write_text(setup_section + "\n" + files_section + "\n" + icons_section + "\n" + run_section, encoding="utf-8")
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

    standalone = Path(args.standalone).expanduser().resolve()
    vst3 = Path(args.vst3).expanduser().resolve()

    if not standalone.exists():
        raise FileNotFoundError(f"Standalone binary '{standalone}' no existe.")
    if not vst3.exists():
        raise FileNotFoundError(f"Plugin VST3 '{vst3}' no existe.")

    output_dir = Path(args.output).expanduser().resolve()
    staging_root = output_dir / "staging" / f"{args.product_name.replace(' ', '')}-{args.version}-{platform_key}"

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

    for runtime in args.python_runtime:
        runtime_path = Path(runtime).expanduser().resolve()
        if not runtime_path.exists():
            raise FileNotFoundError(f"Ruta de Python '{runtime_path}' no existe.")
        dest = staging_root / "Python" / runtime_path.name
        _copy_any(runtime_path, dest)

    install_md = staging_root / "INSTALL.md"
    _write_install_instructions(install_md, platform_key, args.product_name)

    metadata_path = staging_root / "metadata.json"
    _write_metadata(metadata_path, version=args.version, platform_key=platform_key,
                    standalone=standalone, vst3=vst3)

    logo_for_script: Optional[Path] = None
    logo_candidate: Optional[Path]
    if args.logo:
        logo_candidate = Path(args.logo).expanduser().resolve()
        if not logo_candidate.exists():
            raise FileNotFoundError(f"Logo '{logo_candidate}' no existe.")
    else:
        logo_candidate = DEFAULT_LOGO if DEFAULT_LOGO.exists() else None

    if logo_candidate is not None:
        _copy_any(logo_candidate, staging_root / "branding" / logo_candidate.name)
        logo_for_script = logo_candidate

    license_for_script: Optional[Path] = None
    if args.license:
        license_path = Path(args.license).expanduser().resolve()
        if not license_path.exists():
            raise FileNotFoundError(f"Licencia '{license_path}' no existe.")
        license_for_script = license_path

    archives = []
    if not args.skip_archive:
        archives = _create_archives(platform_key, staging_root, output_dir, args.product_name, args.version)

    inno_script = None
    if platform_key == "windows":
        inno_output = output_dir / "windows"
        inno_script = _generate_inno_script(inno_output, product_name=args.product_name, version=args.version,
                                            company=args.company_name, staging_root=staging_root,
                                            logo=logo_for_script, license_file=license_for_script)
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
    }
    print(json.dumps(summary, indent=2))


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Empaqueta los binarios de NeuraSynth en un instalador redistribuible.")
    parser.add_argument("--standalone", required=True, help="Ruta al binario standalone compilado.")
    parser.add_argument("--vst3", required=True, help="Ruta al bundle o archivo VST3.")
    parser.add_argument("--version", required=True, help="Versión del producto (p.ej. 1.0.0).")
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