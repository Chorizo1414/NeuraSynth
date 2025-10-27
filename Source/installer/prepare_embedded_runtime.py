#!/usr/bin/env python3
"""Helper to bootstrap the embedded Python runtime for local debugging.

The script copies the NeuraChord sources next to the embedded interpreter and
adjusts the ``pythonXY._pth`` file so the standard ``Lib``/``site-packages``
directories are honoured. It mirrors the runtime layout expected by
``PythonManager`` and the packaging pipeline.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Iterable

SCRIPT_ROOT = Path(__file__).resolve().parent


def _detect_repo_root(start: Path) -> Path:
    markers = {".git", "NeuraSynth.jucer"}

    for current in [start] + list(start.parents):
        if any((current / marker).exists() for marker in markers):
            return current

    return start


REPO_ROOT = _detect_repo_root(SCRIPT_ROOT)
NEURACHORD_SOURCE = REPO_ROOT / "Source" / "NeuraChord"
PYTHON_DLL_MARKERS: tuple[str, ...] = (
    "python38.dll",
    "python39.dll",
    "python310.dll",
    "python311.dll",
    "python3.dll",
)


def _looks_like_python_runtime(path: Path) -> bool:
    if not path.exists():
        return False

    for marker in PYTHON_DLL_MARKERS:
        if (path / marker).exists():
            return True

    if list(path.glob("python3*.zip")):
        return True

    executables = ("python.exe", "pythonw.exe")
    if any((path / exe).exists() for exe in executables):
        return True

    return False


def _ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _normalise_entries(values: Iterable[str]) -> set[str]:
    return {value.strip().lower().replace("\\", "/") for value in values if value.strip()}


def _configure_embedded_runtime(runtime: Path) -> None:
    """Ensure the embedded runtime honours Lib/site-packages entries."""

    for pth_file in runtime.glob("python*._pth"):
        try:
            original_lines = [line.rstrip("\r\n") for line in pth_file.read_text(encoding="utf-8").splitlines()]
        except OSError:
            continue

        changed = False
        processed_lines = original_lines[:]

        for index, line in enumerate(processed_lines):
            stripped = line.strip().lower()
            if stripped.startswith("# import site"):
                processed_lines[index] = "import site"
                changed = True

        normalised = _normalise_entries(processed_lines)

        def _ensure_entry(value: str) -> None:
            nonlocal changed
            canonical = value.replace("/", "\\")
            if value.lower().replace("/", "/") in normalised:
                return
            if canonical.lower().replace("\\", "/") in normalised:
                return

            try:
                insertion_index = processed_lines.index(".") + 1
            except ValueError:
                insertion_index = len(processed_lines)

            processed_lines.insert(insertion_index, canonical)
            normalised.add(value.lower().replace("/", "/"))
            changed = True

        _ensure_entry("Lib")
        _ensure_entry("Lib/site-packages")

        if changed:
            try:
                pth_file.write_text("\n".join(processed_lines) + "\n", encoding="utf-8")
            except OSError:
                continue


def _copy_neurachord(runtime: Path, *, force: bool) -> Path:
    destination = runtime / "NeuraChord"

    if destination.exists() and force:
        shutil.rmtree(destination)

    if destination.exists():
        return destination

    if not NEURACHORD_SOURCE.exists():
        raise FileNotFoundError(
            f"El directorio de origen '{NEURACHORD_SOURCE}' no existe. Ejecuta este script desde el repositorio completo."
        )

    shutil.copytree(
        NEURACHORD_SOURCE,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", "*.DS_Store"),
    )
    return destination


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configura el runtime embebido para el debugger de Visual Studio.")
    parser.add_argument(
        "runtime",
        type=Path,
        help="Ruta al directorio que contiene pythonXY.dll (por ejemplo Builds/VisualStudio2022/.../Python)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reemplaza el directorio NeuraChord existente dentro del runtime embebido.",
    )
    parser.add_argument(
        "--skip-neurachord",
        action="store_true",
        help="No copia la carpeta NeuraChord (solo ajusta pythonXY._pth).",
    )
    parser.add_argument(
        "--no-pth",
        action="store_true",
        help="Evita modificar archivos pythonXY._pth (úsalo si los personalizaste manualmente).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    runtime = args.runtime.expanduser().resolve()

    if not runtime.exists():
        print(f"[ERROR] La ruta '{runtime}' no existe.")
        return 1

    if not _looks_like_python_runtime(runtime):
        print(
            f"[ADVERTENCIA] '{runtime}' no parece un runtime embebido (no se encontró pythonXY.dll). Se continuará igualmente."
        )

    lib_dir = runtime / "Lib"
    site_packages = lib_dir / "site-packages"

    for folder in (lib_dir, site_packages):
        _ensure_directory(folder)

    if not args.skip_neurachord:
        destination = _copy_neurachord(runtime, force=args.force)
        print(f"[OK] NeuraChord copiado en: {destination}")
    else:
        print("[INFO] Salto la copia de NeuraChord por petición del usuario.")

    if not args.no_pth:
        _configure_embedded_runtime(runtime)
        print("[OK] Archivos pythonXY._pth actualizados (Lib y Lib/site-packages habilitados).")
    else:
        print("[INFO] Archivos pythonXY._pth no modificados.")

    print("[SUGERENCIA] Instala dependencias adicionales dentro de Lib/site-packages según tus necesidades (numpy, music21, etc.).")
    print("[HECHO] Runtime listo para ejecutarse desde Visual Studio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())