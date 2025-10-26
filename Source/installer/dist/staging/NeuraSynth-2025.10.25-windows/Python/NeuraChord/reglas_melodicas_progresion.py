"""Utilidades para aplicar reglas melódicas basadas únicamente en la progresión.

Este módulo encapsula las reglas descritas para la "versión 2" del generador
melódico: todas las notas provienen del acorde activo (triada, séptima y
cualquier tensión declarada), el ritmo se cuantiza completamente a la rejilla y
las velocidades siguen un patrón de acentos fijo.

Las funciones principales permiten elegir notas vecinas dentro del acorde,
controlar el movimiento por índices, cuantizar eventos y evaluar el resultado
con una función objetivo.
"""

from __future__ import annotations

import random
import math
import statistics
from collections import Counter
from difflib import SequenceMatcher
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

ALLOWED_DURATION_UNITS: tuple[int, ...] = (1, 2, 4, 8)


@dataclass
class MovimientoMelodico:
    """Resultado de seleccionar la siguiente nota dentro del conjunto del acorde."""

    midi: int
    indice: int
    direccion: int
    es_salto: bool
    requiere_resolucion: bool


def _ordenar_unicos(conjunto: Iterable[int]) -> List[int]:
    """Devuelve los valores ordenados ascendentemente y sin duplicados."""

    vistos: Dict[int, None] = {}
    for valor in conjunto:
        if valor not in vistos:
            vistos[valor] = None
    return sorted(vistos.keys())


def _indice_mas_cercano(ordenados: Sequence[int], valor: int) -> int:
    return min(range(len(ordenados)), key=lambda idx: abs(ordenados[idx] - valor))


def _nearest_in_list(values: Sequence[int], objetivo: int, prefer_lower: Optional[bool] = None) -> Optional[int]:
    if not values:
        return None
    ordenados = sorted(values)
    if prefer_lower is True:
        candidatos = [v for v in ordenados if v <= objetivo]
        if candidatos:
            return candidatos[-1]
    elif prefer_lower is False:
        candidatos = [v for v in ordenados if v >= objetivo]
        if candidatos:
            return candidatos[0]
    return min(ordenados, key=lambda val: (abs(val - objetivo), val))


def _context_for_segment(progresion: Sequence[Dict[str, object]], indice: int) -> Dict[str, object]:
    if not progresion:
        return {}
    if indice < 0:
        indice = 0
    if indice >= len(progresion):
        indice = len(progresion) - 1
    return progresion[indice]


def _asignar_evento_midi(
    evento: Dict[str, int],
    objetivo: Optional[int],
    contexto: Dict[str, object],
    *,
    prefer_lower: Optional[bool] = None,
) -> Optional[int]:
    if objetivo is None:
        evento["midi"] = None
        evento["index"] = None
        evento["velocity"] = evento.get("velocity", 0)
        return None

    disponibles: Sequence[int] = contexto.get("midi_list", [])  # type: ignore[assignment]
    if not disponibles:
        evento["midi"] = objetivo
        evento["index"] = None
        return objetivo

    valor = _nearest_in_list(disponibles, objetivo, prefer_lower)
    if valor is None:
        valor = disponibles[0]
    evento["midi"] = valor
    try:
        evento["index"] = disponibles.index(valor)
    except ValueError:
        evento["index"] = None
    return valor


def _total_compases(eventos: Sequence[Dict[str, int]], unidades_por_compas: int) -> int:
    if not eventos or unidades_por_compas <= 0:
        return 0
    final_max = 0
    for evento in eventos:
        inicio = evento.get("start", 0)
        dur = evento.get("duration", 0)
        final_max = max(final_max, inicio + max(0, dur))
    if final_max == 0:
        return 0
    return max(1, math.ceil(final_max / unidades_por_compas))


def _dividir_eventos_por_compas(
    eventos: Sequence[Dict[str, int]],
    unidades_por_compas: int,
    total_compases: int,
) -> List[List[Dict[str, int]]]:
    compases: List[List[Dict[str, int]]] = [[] for _ in range(max(1, total_compases))]
    for evento in eventos:
        inicio = evento.get("start", 0)
        compas_idx = 0 if unidades_por_compas <= 0 else min(len(compases) - 1, max(0, inicio // unidades_por_compas))
        compases[compas_idx].append(evento)
    return compases


def _contar_notas_activas(eventos: Sequence[Dict[str, int]]) -> int:
    return sum(1 for evento in eventos if evento.get("midi") is not None)


def _calcular_densidad(
    eventos: Sequence[Dict[str, int]],
    unidades_por_compas: int,
    total_compases: int,
) -> float:
    if not eventos or unidades_por_compas <= 0 or total_compases <= 0:
        return 0.0
    total = unidades_por_compas * total_compases
    ocupacion = sum(evento.get("duration", 0) for evento in eventos if evento.get("midi") is not None)
    return 0.0 if total <= 0 else ocupacion / total


def _orden_para_silenciar(evento: Dict[str, int]) -> tuple:
    beat = evento.get("beat", 0)
    es_fuerte = 1 if beat in (0, 2) else 0
    dur = evento.get("duration", 0)
    inicio = evento.get("start", 0)
    return (es_fuerte, dur, -inicio)


def _convertir_eventos_a_silencio(
    eventos: List[Dict[str, int]],
    indices: List[int],
    cantidad: int,
) -> None:
    if cantidad <= 0:
        return
    for idx in indices:
        if cantidad <= 0:
            break
        evento = eventos[idx]
        evento["midi"] = None
        evento["index"] = None
        evento["velocity"] = evento.get("velocity", 0)
        cantidad -= 1


def _activar_silencios(
    eventos: List[Dict[str, int]],
    progresion: Sequence[Dict[str, object]],
    cantidad: int,
) -> None:
    if cantidad <= 0:
        return
    for idx, evento in enumerate(eventos):
        if cantidad <= 0:
            break
        if evento.get("midi") is not None:
            continue
        contexto = _context_for_segment(progresion, evento.get("segment", 0))
        lista: Sequence[int] = contexto.get("midi_list", [])  # type: ignore[assignment]
        if not lista:
            continue
        objetivo = None
        for prev in reversed(eventos[:idx]):
            if prev.get("midi") is not None:
                objetivo = prev.get("midi")
                break
        if objetivo is None:
            objetivo = lista[len(lista) // 2]
        asignado = _asignar_evento_midi(evento, objetivo, contexto)
        if asignado is not None:
            cantidad -= 1


def _calc_phrase_similarity(
    eventos: Sequence[Dict[str, int]],
    unidades_por_compas: int,
    total_compases: int,
) -> float:
    if total_compases < 2 or unidades_por_compas <= 0:
        return 0.0
    mitad_compases = max(1, total_compases // 2)
    limite = mitad_compases * unidades_por_compas
    frase_a = [evento.get("index") for evento in eventos if evento.get("start", 0) < limite and evento.get("midi") is not None]
    frase_b = [evento.get("index") for evento in eventos if evento.get("start", 0) >= limite and evento.get("midi") is not None]
    if not frase_a or not frase_b:
        return 0.0
    return SequenceMatcher(None, frase_a, frase_b).ratio()


def _calc_repetition_ratio(eventos: Sequence[Dict[str, int]]) -> float:
    indices = [evento.get("index") for evento in eventos if evento.get("midi") is not None]
    if len(indices) < 6:
        return 0.6
    motivo = indices[:3]
    total = 0
    repetidos = 0
    for offset in range(3, len(indices) - 2, 3):
        ventana = indices[offset : offset + 3]
        if len(ventana) < 3:
            continue
        total += 1
        if SequenceMatcher(None, motivo, ventana).ratio() >= 0.7:
            repetidos += 1
    if total == 0:
        return 0.6
    return repetidos / total


def _calc_average_interval(eventos: Sequence[Dict[str, int]]) -> float:
    prev = None
    diferencias: List[int] = []
    for evento in sorted(eventos, key=lambda e: e.get("start", 0)):
        midi = evento.get("midi")
        if midi is None:
            continue
        if prev is not None:
            diferencias.append(abs(midi - prev))
        prev = midi
    if not diferencias:
        return 0.0
    return statistics.mean(diferencias)


def _calc_energy_shape(
    eventos: Sequence[Dict[str, int]],
    total_compases: int,
    unidades_por_compas: int,
) -> float:
    if not eventos or total_compases <= 0 or unidades_por_compas <= 0:
        return 0.0
    total_unidades = total_compases * unidades_por_compas
    mitad = total_unidades / 2
    activos = [evento for evento in eventos if evento.get("midi") is not None]
    if not activos:
        return 0.0
    midis = [evento["midi"] for evento in activos if evento.get("midi") is not None]
    min_midi = min(midis)
    max_midi = max(midis)
    rango = max(1, max_midi - min_midi)
    def energia(evt: Dict[str, int]) -> float:
        midi_norm = (evt.get("midi", min_midi) - min_midi) / rango
        vel = evt.get("velocity", 88) / 127.0
        return midi_norm + vel
    primera = [energia(evt) for evt in activos if evt.get("start", 0) < mitad]
    segunda = [energia(evt) for evt in activos if evt.get("start", 0) >= mitad]
    if not primera or not segunda:
        return 0.0
    ascenso = all(x <= y + 1e-6 for x, y in zip(primera, primera[1:]))
    descenso = all(x >= y - 1e-6 for x, y in zip(segunda, segunda[1:]))
    if ascenso and descenso:
        return 1.0
    media_primera = statistics.mean(primera)
    media_segunda = statistics.mean(segunda)
    if media_primera == 0:
        return 0.0
    if media_segunda <= media_primera:
        return 0.8
    return max(0.0, 1.0 - (media_segunda - media_primera))


def _limitar_paleta_por_frase(
    eventos: Sequence[Dict[str, int]],
    unidades_por_compas: int,
    total_compases: int,
) -> None:
    if total_compases <= 0 or unidades_por_compas <= 0:
        return
    mitad_compases = max(1, total_compases // 2)
    limite = mitad_compases * unidades_por_compas
    for rango_inicio, rango_fin in ((0, limite), (limite, total_compases * unidades_por_compas)):
        frase_indices = [
            idx
            for idx, evento in enumerate(eventos)
            if rango_inicio <= evento.get("start", 0) < rango_fin and evento.get("midi") is not None
        ]
        if not frase_indices:
            continue
        notas = [eventos[idx]["midi"] for idx in frase_indices if eventos[idx].get("midi") is not None]
        contador = Counter(notas)
        principales = [midi for midi, _ in contador.most_common(5)]
        if not principales:
            continue
        for idx in frase_indices:
            evento = eventos[idx]
            midi = evento.get("midi")
            if midi in principales:
                continue
            reemplazo = min(principales, key=lambda val: (abs(val - midi), val))
            evento["midi"] = reemplazo


def _ajustar_velocidades_por_fase(
    eventos: Sequence[Dict[str, int]],
    total_compases: int,
    unidades_por_compas: int,
) -> None:
    if total_compases <= 0 or unidades_por_compas <= 0:
        return
    total_unidades = total_compases * unidades_por_compas
    mitad = total_unidades / 2
    activos = [evento for evento in sorted(eventos, key=lambda e: e.get("start", 0)) if evento.get("midi") is not None]
    if not activos:
        return
    primera = [evt for evt in activos if evt.get("start", 0) < mitad]
    segunda = [evt for evt in activos if evt.get("start", 0) >= mitad]
    for idx, evento in enumerate(primera):
        evento["velocity"] = min(127, 76 + int(40 * idx / max(1, len(primera) - 1)))
    for idx, evento in enumerate(segunda):
        evento["velocity"] = max(64, 96 - int(40 * idx / max(1, len(segunda))))


def _aplicar_limite_y_densidad(
    eventos: List[Dict[str, int]],
    progresion: Sequence[Dict[str, object]],
    unidades_por_compas: int,
    total_compases: int,
) -> None:
    if not eventos or total_compases <= 0:
        return
    max_notas = 8 * total_compases
    activos = [idx for idx, evento in enumerate(eventos) if evento.get("midi") is not None]
    if len(activos) > max_notas:
        candidatos = sorted(activos, key=lambda idx: _orden_para_silenciar(eventos[idx]))
        _convertir_eventos_a_silencio(eventos, candidatos, len(activos) - max_notas)
    densidad = _calcular_densidad(eventos, unidades_por_compas, total_compases)
    if densidad > 0.6:
        while densidad > 0.6:
            activos = [idx for idx, evento in enumerate(eventos) if evento.get("midi") is not None]
            if not activos:
                break
            candidatos = sorted(activos, key=lambda idx: _orden_para_silenciar(eventos[idx]))
            _convertir_eventos_a_silencio(eventos, candidatos, 1)
            densidad = _calcular_densidad(eventos, unidades_por_compas, total_compases)
    elif densidad < 0.4:
        deficit = 0.4 - densidad
        cantidad = max(1, math.ceil(deficit * unidades_por_compas * total_compases / max(1, unidades_por_compas)))
        _activar_silencios(eventos, progresion, cantidad)


def _ajustar_pregunta_respuesta(
    eventos: List[Dict[str, int]],
    progresion: Sequence[Dict[str, object]],
    unidades_por_compas: int,
    total_compases: int,
) -> None:
    if total_compases < 2:
        return
    frase_compases = 2 if total_compases >= 4 else max(1, total_compases // 2)
    limite = frase_compases * unidades_por_compas
    frase_a = [evento for evento in eventos if evento.get("start", 0) < limite]
    frase_b = [evento for evento in eventos if evento.get("start", 0) >= limite]
    if not frase_a or not frase_b:
        return
    mean_a = statistics.mean(
        [evento["midi"] for evento in frase_a if evento.get("midi") is not None]
    ) if any(evt.get("midi") is not None for evt in frase_a) else None
    mean_b = statistics.mean(
        [evento["midi"] for evento in frase_b if evento.get("midi") is not None]
    ) if any(evt.get("midi") is not None for evt in frase_b) else None
    ultima_a = next((evt for evt in reversed(frase_a) if evt.get("midi") is not None), None)
    if ultima_a is not None:
        contexto = _context_for_segment(progresion, ultima_a.get("segment", 0))
        triada: Sequence[int] = contexto.get("triad", [])  # type: ignore[assignment]
        objetivos = list(triada[1:3]) if len(triada) >= 2 else list(triada)
        if not objetivos:
            objetivos = contexto.get("midi_list", [])  # type: ignore[assignment]
        if objetivos:
            objetivo = min(objetivos, key=lambda val: abs(val - ultima_a.get("midi", objetivos[0])))
            _asignar_evento_midi(ultima_a, objetivo, contexto)
    ultima_b = next((evt for evt in reversed(frase_b) if evt.get("midi") is not None), None)
    if ultima_b is not None:
        contexto = _context_for_segment(progresion, ultima_b.get("segment", 0))
        triada: Sequence[int] = contexto.get("triad", [])  # type: ignore[assignment]
        if triada:
            _asignar_evento_midi(ultima_b, triada[0], contexto)
    if mean_a is not None and mean_b is not None and mean_b >= mean_a:
        for evento in frase_b:
            if evento.get("midi") is None:
                continue
            contexto = _context_for_segment(progresion, evento.get("segment", 0))
            _asignar_evento_midi(evento, evento.get("midi") - 1, contexto, prefer_lower=True)
    similitud = _calc_phrase_similarity(eventos, unidades_por_compas, total_compases)
    if similitud < 0.4:
        base = [evt for evt in frase_a if evt.get("midi") is not None]
        variacion = [evt for evt in frase_b if evt.get("midi") is not None]
        for idx, (fuente, destino) in enumerate(zip(base, variacion)):
            contexto = _context_for_segment(progresion, destino.get("segment", 0))
            offset = -1 if idx % 2 else 0
            objetivo = fuente.get("midi")
            if objetivo is None:
                continue
            _asignar_evento_midi(destino, objetivo + offset, contexto)
    elif similitud > 0.7:
        variacion = [evt for evt in frase_b if evt.get("midi") is not None]
        for idx, destino in enumerate(variacion):
            contexto = _context_for_segment(progresion, destino.get("segment", 0))
            objetivo = destino.get("midi")
            if objetivo is None:
                continue
            shift = -1 if idx % 2 == 0 else 1
            _asignar_evento_midi(destino, objetivo + shift, contexto)


def _controlar_intervalos(
    eventos: List[Dict[str, int]],
    progresion: Sequence[Dict[str, object]],
) -> None:
    prev = None
    for evento in sorted(eventos, key=lambda e: e.get("start", 0)):
        midi = evento.get("midi")
        if midi is None:
            continue
        if prev is not None and abs(midi - prev) > 3:
            contexto = _context_for_segment(progresion, evento.get("segment", 0))
            nuevo = _asignar_evento_midi(evento, prev, contexto, prefer_lower=midi > prev)
            if nuevo is None or abs(nuevo - prev) > 3:
                evento["midi"] = None
                evento["index"] = None
                prev = prev
                continue
            midi = nuevo
        prev = midi


def _asegurar_coherencia_local(
    eventos: List[Dict[str, int]],
    progresion: Sequence[Dict[str, object]],
    unidades_por_compas: int,
) -> None:
    if unidades_por_compas <= 0:
        return
    unidades_por_tiempo = unidades_por_compas // 4 if unidades_por_compas >= 4 else 1
    eventos_ordenados = sorted(eventos, key=lambda e: e.get("start", 0))
    prev_evento = None
    for evento in eventos_ordenados:
        midi = evento.get("midi")
        if midi is None:
            continue
        if prev_evento is not None:
            delta_inicio = evento.get("start", 0) - prev_evento.get("start", 0)
            contexto = _context_for_segment(progresion, evento.get("segment", 0))
            if delta_inicio < unidades_por_tiempo and prev_evento.get("midi") is not None:
                objetivo = prev_evento.get("midi")
                if objetivo is not None:
                    if midi > objetivo + 1:
                        _asignar_evento_midi(evento, objetivo + 1, contexto)
                    elif midi < objetivo - 1:
                        _asignar_evento_midi(evento, objetivo - 1, contexto)
            elif delta_inicio >= unidades_por_tiempo and prev_evento.get("midi") is not None:
                objetivo = prev_evento.get("midi")
                if objetivo is not None and abs(midi - objetivo) > 2:
                    prefer_lower = midi > objetivo
                    _asignar_evento_midi(evento, objetivo + (-2 if prefer_lower else 2), contexto)
        prev_evento = evento


def _aplicar_paleta_reducida(
    eventos: List[Dict[str, int]],
    unidades_por_compas: int,
    total_compases: int,
) -> None:
    _limitar_paleta_por_frase(eventos, unidades_por_compas, total_compases)


def _aplicar_resolucion_percibida(
    eventos: List[Dict[str, int]],
    progresion: Sequence[Dict[str, object]],
    unidades_por_compas: int,
) -> None:
    if not eventos:
        return
    ultimo = max(eventos, key=lambda e: e.get("start", 0) + e.get("duration", 0))
    contexto = _context_for_segment(progresion, ultimo.get("segment", 0))
    duraciones = [evt.get("duration", 0) for evt in eventos if evt.get("midi") is not None]
    if duraciones:
        promedio = statistics.mean(duraciones)
        ultimo["duration"] = max(ultimo.get("duration", 0), int(round(promedio * 2)))
        unidades_restantes = unidades_por_compas - (ultimo.get("start", 0) % max(1, unidades_por_compas))
        if unidades_restantes > 0:
            ultimo["duration"] = min(ultimo.get("duration", 0), unidades_restantes)
    velocidades = [evt.get("velocity", 88) for evt in eventos if evt.get("midi") is not None]
    if velocidades:
        promedio_vel = statistics.mean(velocidades)
        ultimo["velocity"] = int(max(40, min(ultimo.get("velocity", promedio_vel), promedio_vel * 0.9)))
    triada: Sequence[int] = contexto.get("triad", [])  # type: ignore[assignment]
    if triada:
        _asignar_evento_midi(ultimo, triada[0], contexto)


def aplicar_reglas_avanzadas(
    eventos: List[Dict[str, int]],
    progresion: Sequence[Dict[str, object]],
    *,
    unidades_por_compas: Optional[int] = None,
) -> None:
    if not eventos:
        return
    if unidades_por_compas is None:
        if progresion:
            unidades_por_compas = int(progresion[0].get("units_per_bar", 16))  # type: ignore[arg-type]
        else:
            unidades_por_compas = 16
    total_compases = _total_compases(eventos, unidades_por_compas)
    if total_compases <= 0:
        return
    _aplicar_limite_y_densidad(eventos, progresion, unidades_por_compas, total_compases)
    _ajustar_pregunta_respuesta(eventos, progresion, unidades_por_compas, total_compases)
    _controlar_intervalos(eventos, progresion)
    _asegurar_coherencia_local(eventos, progresion, unidades_por_compas)
    _aplicar_paleta_reducida(eventos, unidades_por_compas, total_compases)
    _ajustar_velocidades_por_fase(eventos, total_compases, unidades_por_compas)
    _aplicar_resolucion_percibida(eventos, progresion, unidades_por_compas)
def _filtrar_por_direccion(
    indices: List[int],
    referencia: int,
    direccion: Optional[int],
) -> List[int]:
    if direccion is None or direccion == 0:
        return indices
    resultado = [idx for idx in indices if (idx - referencia) * direccion > 0]
    return resultado or indices


def _ordenar_por_objetivo(
    indices: List[int],
    referencia: int,
    objetivo: Optional[int],
) -> List[int]:
    if objetivo is None:
        # Ordenar por cercanía al índice de referencia para mantener pasos cortos.
        return sorted(indices, key=lambda idx: abs(idx - referencia))
    return sorted(
        indices,
        key=lambda idx: (
            abs(idx - objetivo),
            abs(idx - referencia),
        ),
    )


def variar_por_indice(
    nota_anterior: Optional[int],
    S_k: Sequence[int],
    p_pasos: float = 0.8,
    max_salto: int = 2,
    resolver: bool = True,
    *,
    subset: Optional[Sequence[int]] = None,
    ultima_direccion: Optional[int] = None,
    direccion_preferida: Optional[int] = None,
    objetivo: Optional[int] = None,
) -> MovimientoMelodico:
    """Selecciona la siguiente nota dentro de ``S_k`` respetando los índices."""

    if not S_k:
        raise ValueError("S_k no puede estar vacío")

    orden = _ordenar_unicos(S_k)
    indice_por_midi = {valor: idx for idx, valor in enumerate(orden)}

    if subset:
        indices_disponibles = [indice_por_midi[valor] for valor in subset if valor in indice_por_midi]
    else:
        indices_disponibles = list(indice_por_midi.values())

    if not indices_disponibles:
        indices_disponibles = list(indice_por_midi.values())

    if nota_anterior is None:
        if objetivo is not None and 0 <= objetivo < len(orden):
            indice_actual = objetivo
        else:
            indice_actual = indices_disponibles[len(indices_disponibles) // 2]
    else:
        indice_actual = indice_por_midi.get(nota_anterior)
        if indice_actual is None:
            indice_actual = _indice_mas_cercano(orden, nota_anterior)

    pasos = [idx for idx in indices_disponibles if abs(idx - indice_actual) <= 1]
    saltos = [idx for idx in indices_disponibles if 1 < abs(idx - indice_actual) <= max_salto]

    pasos = _filtrar_por_direccion(pasos, indice_actual, direccion_preferida)
    saltos = _filtrar_por_direccion(saltos, indice_actual, direccion_preferida)

    usar_salto = False
    if nota_anterior is None:
        usar_salto = False
    elif saltos:
        if objetivo is not None and abs(objetivo - indice_actual) >= 2:
            usar_salto = True
        else:
            usar_salto = random.random() > p_pasos

    candidatos = saltos if usar_salto else pasos
    if not candidatos:
        candidatos = saltos or pasos or indices_disponibles

    candidatos = _ordenar_por_objetivo(list(candidatos), indice_actual, objetivo)

    if ultima_direccion in (-1, 1) and candidatos:
        preferidos = [idx for idx in candidatos if (idx - indice_actual) * ultima_direccion < 0 or abs(idx - indice_actual) <= 1]
        if preferidos:
            candidatos = preferidos

    indice_nuevo = candidatos[0]
    direccion = 0 if indice_nuevo == indice_actual else (1 if indice_nuevo > indice_actual else -1)
    es_salto = abs(indice_nuevo - indice_actual) >= 2
    requiere_resolucion = resolver and es_salto and direccion != 0

    midi = orden[indice_nuevo]
    return MovimientoMelodico(midi, indice_nuevo, direccion, es_salto, requiere_resolucion)


def elegir_vecina(
    nota_anterior: Optional[int],
    T_k: Sequence[int],
    S_k: Sequence[int],
    *,
    objetivo: Optional[int] = None,
    ultima_direccion: Optional[int] = None,
    direccion_preferida: Optional[int] = None,
) -> MovimientoMelodico:
    """Elige una nota vecina dentro de la triada/séptima (tiempos fuertes)."""

    return variar_por_indice(
        nota_anterior,
        S_k,
        p_pasos=1.0,
        max_salto=1,
        resolver=False,
        subset=T_k,
        ultima_direccion=ultima_direccion,
        direccion_preferida=direccion_preferida,
        objetivo=objetivo,
    )


def cuantizar_y_accentos(
    eventos: List[Dict[str, int]],
    grid: float = 1 / 16,
    velocity_levels: Optional[Sequence[int]] = None,
) -> List[Dict[str, int]]:
    """Cuantiza inicio/duración y asigna velocities discretas."""

    if velocity_levels:
        niveles = sorted(set(int(v) for v in velocity_levels))
    else:
        niveles = [76, 88, 100, 112]

    base = niveles[min(len(niveles) - 1, len(niveles) // 2)]
    fuerte = niveles[-1]
    medio = niveles[-2] if len(niveles) > 1 else niveles[-1]

    unidades_por_tiempo = max(1, int(round(1.0 / grid)))

    for evento in eventos:
        evento["start"] = int(round(evento.get("start", 0)))
        evento["duration"] = max(1, int(round(evento.get("duration", 1))))
        beat = int((evento["start"] // unidades_por_tiempo) % 4)
        evento["beat"] = beat
        if beat == 0:
            evento["velocity"] = fuerte
        elif beat == 2:
            evento["velocity"] = medio
        else:
            evento["velocity"] = base
    return eventos


def forzar_resolucion(
    evento_final: Dict[str, int],
    T_k_final: Sequence[int],
    S_k: Optional[Sequence[int]] = None,
    prioridad: Sequence[int] = (1, 3, 5),
) -> Dict[str, int]:
    """Ajusta la nota final para que resuelva en 1ª, 3ª o 5ª."""

    if not evento_final or "midi" not in evento_final or evento_final["midi"] is None:
        return evento_final

    triada = _ordenar_unicos(T_k_final)
    if not triada:
        return evento_final

    indice_por_midi = None
    if S_k:
        orden = _ordenar_unicos(S_k)
        indice_por_midi = {valor: idx for idx, valor in enumerate(orden)}

    prioridad_indices = {1: 0, 3: 1, 5: 2}
    for grado in prioridad:
        idx_triada = prioridad_indices.get(grado)
        if idx_triada is None or idx_triada >= len(triada):
            continue
        midi_objetivo = triada[idx_triada]
        evento_final["midi"] = midi_objetivo
        if indice_por_midi and midi_objetivo in indice_por_midi:
            evento_final["indice"] = indice_por_midi[midi_objetivo]
        return evento_final

    midi_actual = evento_final["midi"]
    midi_cercano = min(triada, key=lambda valor: abs(valor - midi_actual))
    evento_final["midi"] = midi_cercano
    if indice_por_midi and midi_cercano in indice_por_midi:
        evento_final["indice"] = indice_por_midi[midi_cercano]
    return evento_final


def evaluar_melodia(
    eventos: Sequence[Dict[str, int]],
    progresion: Sequence[Dict[str, object]],
) -> Dict[str, float]:
    """Evalúa la melodía con las métricas clásicas y las reglas de pegajosidad."""

    if not eventos:
        return {
            "score": 0.0,
            "harmonic": 0.0,
            "movement": 0.0,
            "rhythm": 0.0,
            "coherence": 0.0,
            "repetition": 0.0,
            "simplicity": 0.0,
            "coherence_local": 0.0,
            "history": 0.0,
            "density": 0.0,
            "phrase_similarity": 0.0,
            "note_ratio": 0.0,
        }

    unidades_por_compas = int(progresion[0].get("units_per_bar", 16)) if progresion else 16
    total_compases = _total_compases(eventos, unidades_por_compas)
    total_duracion = sum(evento.get("duration", 0) for evento in eventos if evento.get("midi") is not None)
    if total_duracion <= 0 or total_compases <= 0:
        return {
            "score": 0.0,
            "harmonic": 0.0,
            "movement": 0.0,
            "rhythm": 0.0,
            "coherence": 0.0,
            "repetition": 0.0,
            "simplicity": 0.0,
            "coherence_local": 0.0,
            "history": 0.0,
            "density": 0.0,
            "phrase_similarity": 0.0,
            "note_ratio": 0.0,
        }

    # Componente armónica (H)
    duracion_armonica = 0
    for evento in eventos:
        midi = evento.get("midi")
        if midi is None:
            continue
        segmento = evento.get("segment", 0)
        if segmento >= len(progresion):
            segmento = len(progresion) - 1
        if segmento < 0:
            segmento = 0
        conjunto = progresion[segmento].get("S", set())
        if midi in conjunto:
            duracion_armonica += evento.get("duration", 0)
    harmonic = duracion_armonica / total_duracion if total_duracion else 0.0

    # Movimiento controlado
    penalizaciones = 0.0
    ultimo_indice = None
    for evento in eventos:
        indice = evento.get("index")
        if indice is None:
            continue
        if ultimo_indice is None:
            ultimo_indice = indice
            continue
        diferencia = indice - ultimo_indice
        if abs(diferencia) > 1:
            penalizaciones += abs(diferencia) - 1
            if abs(diferencia) > 2:
                penalizaciones += 0.5
        ultimo_indice = indice
    movement = max(0.0, 1.0 - 0.2 * penalizaciones)

    # Ritmo cuantizado
    duracion_por_compas: Dict[int, int] = {}
    for evento in eventos:
        dur = evento.get("duration", 0)
        if dur <= 0:
            continue
        compas = evento.get("start", 0) // unidades_por_compas if unidades_por_compas else 0
        duracion_por_compas[compas] = duracion_por_compas.get(compas, 0) + dur
    if duracion_por_compas:
        errores = sum(abs(total - unidades_por_compas) for total in duracion_por_compas.values())
        rhythm = max(0.0, 1.0 - errores / (unidades_por_compas * len(duracion_por_compas)))
    else:
        rhythm = 0.0
    desajuste = sum(
        evento.get("duration", 0)
        for evento in eventos
        if evento.get("duration", 0) not in ALLOWED_DURATION_UNITS
    )
    if total_duracion:
        rhythm *= max(0.0, 1.0 - desajuste / total_duracion)

    # Coherencia de motivos (legacy)
    motivo_len = 3
    patrones: Dict[tuple, int] = {}
    for idx in range(len(eventos) - motivo_len + 1):
        ventana = tuple(eventos[idx + j].get("index") for j in range(motivo_len))
        if None in ventana:
            continue
        patrones[ventana] = patrones.get(ventana, 0) + 1
    coherence = max(patrones.values()) / sum(patrones.values()) if patrones else 0.6

    # Métricas nuevas
    density = _calcular_densidad(eventos, unidades_por_compas, total_compases)
    active_notes = _contar_notas_activas(eventos)
    note_ratio = active_notes / (8 * total_compases) if total_compases else 0.0
    phrase_similarity = _calc_phrase_similarity(eventos, unidades_por_compas, total_compases)
    repetition = _calc_repetition_ratio(eventos)
    unique_notes = len({evento.get("midi") for evento in eventos if evento.get("midi") is not None})
    simplicity_density = 1.0 if 0.4 <= density <= 0.6 else max(0.0, 1.0 - abs(density - 0.5))
    simplicity_unique = 1.0 if unique_notes <= 5 else max(0.0, 1.0 - (unique_notes - 5) / 5.0)
    simplicity = simplicity_density * simplicity_unique
    avg_interval = _calc_average_interval(eventos)
    coherence_local = max(0.0, 1.0 - max(0.0, avg_interval - 1.0) / 4.0)
    history = _calc_energy_shape(eventos, total_compases, unidades_por_compas)

    score = 0.3 * repetition + 0.2 * simplicity + 0.2 * coherence_local + 0.3 * history

    return {
        "score": score,
        "harmonic": harmonic,
        "movement": movement,
        "rhythm": rhythm,
        "coherence": coherence,
        "repetition": repetition,
        "simplicity": simplicity,
        "coherence_local": coherence_local,
        "history": history,
        "density": density,
        "phrase_similarity": phrase_similarity,
        "note_ratio": note_ratio,
    }


__all__ = [
    "MovimientoMelodico",
    "elegir_vecina",
    "variar_por_indice",
    "cuantizar_y_accentos",
    "forzar_resolucion",
    "aplicar_reglas_avanzadas",
    "evaluar_melodia",
]