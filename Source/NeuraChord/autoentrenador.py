"""Herramienta de auto entrenamiento para NeuraChord.

Este script analiza los archivos MIDI de la carpeta ``MIDI_APRENDER`` y
extrae progresiones armónicas, patrones rítmicos, silencios y la tonalidad
dominante. La información obtenida se integra en los archivos
``estilos/base_<genero>.py`` siguiendo la misma estructura utilizada por el
generador de acordes.

Uso básico::

    python autoentrenador.py --genero pop

Opcionalmente se puede indicar una carpeta distinta a ``MIDI_APRENDER`` con
``--carpeta``.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import pprint
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple, Union

from music21 import chord, converter, duration, key, note, roman, stream


# ---------------------------------------------------------------------------
# Tipos y utilidades
# ---------------------------------------------------------------------------

NotaEvento = Union[str, Tuple[str, ...]]


@dataclass(frozen=True)
class ProgresionNormalizada:
    """Representa una progresión para poder detectar duplicados."""

    acordes: Tuple[NotaEvento, ...]
    ritmo: Tuple[float, ...]


def _ruta_estilos() -> str:
    return os.path.join(os.path.dirname(__file__), "estilos")


def _ruta_archivo_genero(nombre_genero: str) -> str:
    return os.path.join(_ruta_estilos(), f"base_{nombre_genero}.py")


def _cargar_info_genero(nombre_genero: str) -> Dict:
    """Carga (o crea) la estructura INFO_GENERO para ``nombre_genero``."""

    ruta_archivo = _ruta_archivo_genero(nombre_genero)
    info_genero = {}

    if os.path.exists(ruta_archivo):
        modulo_name = f"autoentrenador_base_{nombre_genero}"
        spec = importlib.util.spec_from_file_location(modulo_name, ruta_archivo)
        if spec and spec.loader:
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
            info_genero = getattr(modulo, "INFO_GENERO", {})
        else:
            print(f"[ADVERTENCIA] No fue posible cargar {ruta_archivo}. Se creará uno nuevo.")

    if nombre_genero not in info_genero:
        info_genero[nombre_genero] = {}

    if "patrones_ritmicos" not in info_genero[nombre_genero]:
        info_genero[nombre_genero]["patrones_ritmicos"] = []

    return info_genero


def _guardar_info_genero(nombre_genero: str, info_genero: Dict) -> None:
    ruta_archivo = _ruta_archivo_genero(nombre_genero)
    os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
    with open(ruta_archivo, "w", encoding="utf-8") as f:
        f.write(f"# Archivo de estilo para {nombre_genero}\n")
        f.write("# Contiene modelos de Markov, patrones rítmicos y progresiones aprendidas.\n\n")
        f.write("INFO_GENERO = ")
        f.write(pprint.pformat(info_genero, indent=4, width=120, sort_dicts=False))


def _tonalidad_desde_analisis(analisis_key: key.Key) -> str:
    tonic = analisis_key.tonic.name.lower().replace("-", "b")
    modo = analisis_key.mode.lower()
    return f"{tonic} {modo}"


def _normalizar_acorde(evento: Union[chord.Chord, note.Note, note.Rest]) -> NotaEvento:
    """Convierte un evento musical en el formato utilizado por INFO_GENERO."""

    if isinstance(evento, note.Rest):
        return "0"

    if isinstance(evento, note.Note):
        return f"SN_{evento.nameWithOctave}"

    if isinstance(evento, chord.Chord):
        notas = tuple(sorted(n.nameWithOctave for n in evento.notes))
        if len(notas) == 1:
            return f"SN_{notas[0]}"
        return notas

    raise TypeError(f"Evento no soportado: {type(evento)}")


def _duracion_en_negras(evento: Union[chord.Chord, note.Note, note.Rest]) -> float:
    dur: duration.Duration = evento.duration
    return float(dur.quarterLength)


def _roman_de_evento(evento: Union[chord.Chord, note.Note, note.Rest], tonalidad: key.Key) -> str:
    if isinstance(evento, note.Rest):
        return "0"

    if isinstance(evento, note.Note):
        return f"SN_{evento.nameWithOctave}"

    if isinstance(evento, chord.Chord):
        try:
            rn = roman.romanNumeralFromChord(evento, tonalidad)
            return rn.figure
        except Exception:
            # Fallback a representación textual del acorde
            try:
                return evento.commonName or evento.root().name
            except Exception:
                return "acorde"

    return "?"


def _normalizar_existente(entries: Iterable[Dict]) -> Dict[ProgresionNormalizada, Dict]:
    normalizados: Dict[ProgresionNormalizada, Dict] = {}
    for entry in entries:
        acordes_brutos = entry.get("chords", [])
        ritmo_bruto = entry.get("rhythm", [])

        acordes_normalizados: List[NotaEvento] = []
        for acorde in acordes_brutos:
            if isinstance(acorde, (list, tuple)):
                acordes_normalizados.append(tuple(acorde))
            else:
                acordes_normalizados.append(acorde)

        clave = ProgresionNormalizada(tuple(acordes_normalizados), tuple(map(float, ritmo_bruto)))
        normalizados[clave] = entry

    return normalizados


def _procesar_stream_midi(midi_stream: stream.Stream) -> Tuple[key.Key, List[NotaEvento], List[str], List[float]]:
    analisis = midi_stream.analyze("key")
    acorde_stream = midi_stream.chordify().flat

    acordes: List[NotaEvento] = []
    romanos: List[str] = []
    ritmos: List[float] = []

    for evento in acorde_stream:
        if not isinstance(evento, (chord.Chord, note.Note, note.Rest)):
            continue

        duracion = _duracion_en_negras(evento)
        if duracion <= 0:
            continue

        acordes.append(_normalizar_acorde(evento))
        ritmos.append(duracion)
        romanos.append(_roman_de_evento(evento, analisis))

    return analisis, acordes, romanos, ritmos


def _actualizar_modelo(modelo_tonalidad: Dict, romanos: Sequence[str]) -> None:
    modelo_tonalidad.setdefault("markov_transitions", {})
    modelo_tonalidad.setdefault("start_chords", {})
    modelo_tonalidad.setdefault("end_chords", {})

    if romanos:
        inicio = romanos[0]
        modelo_tonalidad["start_chords"][inicio] = modelo_tonalidad["start_chords"].get(inicio, 0) + 1

        fin = romanos[-1]
        modelo_tonalidad["end_chords"][fin] = modelo_tonalidad["end_chords"].get(fin, 0) + 1

    for actual, siguiente in zip(romanos, romanos[1:]):
        transiciones = modelo_tonalidad["markov_transitions"].setdefault(actual, {})
        transiciones[siguiente] = transiciones.get(siguiente, 0) + 1


def _imprimir_resumen(nombre_archivo: str, tonalidad: key.Key, acordes: Sequence[NotaEvento], romanos: Sequence[str], ritmos: Sequence[float]) -> None:
    print("\n======================================================")
    print(f"Archivo: {nombre_archivo}")
    print(f"Tonalidad detectada: {tonalidad.tonic.name} {tonalidad.mode}")
    print("Secuencia (voicings):")
    for idx, acorde in enumerate(acordes, start=1):
        print(f"  {idx:02d}. {acorde}")
    print("Secuencia (romanos / silencios / notas sueltas):")
    for idx, rn in enumerate(romanos, start=1):
        print(f"  {idx:02d}. {rn}")
    print("Patrón rítmico (en negras):", ritmos)


def entrenar_genero(desde_carpeta: str, nombre_genero: str) -> None:
    ruta_carpeta = os.path.abspath(desde_carpeta)
    if not os.path.isdir(ruta_carpeta):
        raise FileNotFoundError(f"La carpeta '{ruta_carpeta}' no existe")

    info_genero = _cargar_info_genero(nombre_genero)
    almacen = info_genero[nombre_genero]

    archivos_midi = [
        os.path.join(ruta_carpeta, archivo)
        for archivo in os.listdir(ruta_carpeta)
        if archivo.lower().endswith((".mid", ".midi"))
    ]

    if not archivos_midi:
        print("No se encontraron archivos MIDI para entrenar.")
        return

    archivos_midi.sort()

    for ruta_midi in archivos_midi:
        try:
            midi_stream = converter.parse(ruta_midi)
        except Exception as exc:
            print(f"[ERROR] No se pudo analizar '{ruta_midi}': {exc}")
            continue

        tonalidad, acordes, romanos, ritmos = _procesar_stream_midi(midi_stream)

        if not acordes:
            print(f"[ADVERTENCIA] '{ruta_midi}' no produjo acordes reconocibles. Se omite.")
            continue

        tonalidad_clave = _tonalidad_desde_analisis(tonalidad)
        modelo_tonalidad = almacen.setdefault(
            tonalidad_clave,
            {
                "markov_transitions": {},
                "start_chords": {},
                "end_chords": {},
                "learned_progressions": [],
            },
        )

        existentes = _normalizar_existente(modelo_tonalidad.get("learned_progressions", []))
        progresion_actual = ProgresionNormalizada(tuple(acordes), tuple(ritmos))

        if progresion_actual in existentes:
            print(f"[INFO] '{os.path.basename(ruta_midi)}' ya estaba entrenado. Se omite.")
            continue

        modelo_tonalidad.setdefault("learned_progressions", []).append(
            {"chords": list(acordes), "rhythm": list(ritmos)}
        )

        _actualizar_modelo(modelo_tonalidad, romanos)

        patrones = almacen.setdefault("patrones_ritmicos", [])
        if list(ritmos) not in patrones:
            patrones.append(list(ritmos))

        _imprimir_resumen(os.path.basename(ruta_midi), tonalidad, acordes, romanos, ritmos)

    _guardar_info_genero(nombre_genero, info_genero)
    print("\nEntrenamiento completado. Datos guardados en:", _ruta_archivo_genero(nombre_genero))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto entrenador de progresiones para NeuraChord")
    parser.add_argument("--genero", required=True, help="Nombre del género musical (ej. pop, jazz)")
    parser.add_argument(
        "--carpeta",
        default=os.path.join(os.path.dirname(__file__), "MIDI_APRENDER"),
        help="Ruta a la carpeta con archivos MIDI a analizar",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    entrenar_genero(args.carpeta, args.genero)


if __name__ == "__main__":
    main()