# main.py
import tkinter as tk
from tkinter import ttk, StringVar, filedialog, simpledialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD # type: ignore
from PIL import Image, ImageTk
import re
import random
import os
import shutil
import subprocess
import sys # Necesario para resource_path y la lógica del icono
import pygame
from music21 import key, stream, chord, midi, note, harmony, instrument, scale
from music21.tempo import MetronomeMark

# Importaciones de módulos locales
from base_estilos import INFO_GENERO
from generos import detectar_estilo
from generador_acordes import (
    extraer_tonalidad,
    generar_progresion_acordes_smart,
    set_generator_mode,
    reset_learned_prog_index,
    transponer_progresion,
    limpiar_nombre_acorde,
    reforzar_progresion_con_feedback,
    nota_equivalente
)
from generador_melodia import generar_melodia_sobre_acordes
from piano_roll_visualizer import PianoRoll
from procesador_sentimientos import detectar_sentimiento_en_prompt, inferir_parametros_desde_sentimiento


# --- Colores y Fuentes ---
COLOR_BG_VENTANA = "#1d1d1d"; COLOR_BG_FRAMES = "#2E2E2E"
COLOR_FG_TEXT_PRINCIPAL = "#E5E5E5"; COLOR_FG_TEXT_SECUNDARIO = "#CCCBCB"
COLOR_INPUT_BG = "#3C3C3C"; COLOR_INPUT_FG = COLOR_FG_TEXT_PRINCIPAL
COLOR_INPUT_INSERT = COLOR_FG_TEXT_PRINCIPAL
COLOR_BOTON_ACCENTO_BG = "#386FDE"
COLOR_BOTON_ACCENTO_FG = "#FFFFFF"; COLOR_BOTON_ACCENTO_ACTIVE_BG = "#2D5AB5"
COLOR_BOTON_SECUNDARIO_BG = "#4A4A4A"; COLOR_BOTON_SECUNDARIO_FG = COLOR_FG_TEXT_PRINCIPAL
COLOR_BOTON_SECUNDARIO_ACTIVE_BG = "#4A4A4A"; COLOR_BOTON_CONTROL_BG = "#424141"
COLOR_BOTON_CONTROL_FG = COLOR_FG_TEXT_SECUNDARIO; COLOR_BOTON_CONTROL_ACTIVE_BG = "#484848"
COLOR_BOTON_INSTRUMENTO_BG = COLOR_BOTON_CONTROL_BG; COLOR_BOTON_INSTRUMENTO_FG = COLOR_FG_TEXT_SECUNDARIO
COLOR_BOTON_INSTRUMENTO_ACTIVE_BG = COLOR_BOTON_CONTROL_ACTIVE_BG; COLOR_PIANO_ROLL_BG = "#1C1C1C"
COLOR_BOTON_PAUSA_BG = "#CA5151"; COLOR_BOTON_PAUSA_FG = "#FFFFFF"; COLOR_BOTON_PAUSA_ACTIVE_BG = "#B84A4A"
COLOR_TRANSPOSICION_FG = "#FFFFFF"
COLOR_FEEDBACK_POSITIVO_BG = "#3CC85F"
COLOR_FEEDBACK_POSITIVO_FG = "#FFFFFF"
COLOR_FEEDBACK_POSITIVO_ACTIVE_BG = "#35B755"
COLOR_FEEDBACK_NEGATIVO_BG = "#C33A48"
COLOR_FEEDBACK_NEGATIVO_FG = "#FFFFFF"
COLOR_FEEDBACK_NEGATIVO_ACTIVE_BG = "#BC3946"
COLOR_DIALOGO_BG = "#252525"
COLOR_DIALOGO_FG = "#E0E0E0"
COLOR_DIALOGO_LISTA_BG = "#303030"
COLOR_DIALOGO_ERROR_FG = "#FF6B6B"

# --- Mapeo de BPM por Género ---
# (min_bpm, max_bpm, default_bpm_sugerido)
MAPEO_GENERO_BPM = {
    "jazz": (80, 120, 100),
    "lofi": (70, 90, 80),
    "r&b": (60, 110, 90), # Amplio, 90 como punto medio
    "vals": (84, 180, 120),
    "pop": (100, 130, 115),
    "techno": (125, 140, 130),
    "reggaeton": (85, 100, 95),
    # Añade más géneros y sus BPMs aquí si es necesario
    "normal": (80, 120, 100) # Un default si el género es "normal"
}


# --- Variables Globales ---
bpm_actual = 100 # Valor inicial, se actualizará
ultima_raiz = None
ultimo_modo = None
ultimo_estilo_generado = None
cantidad_acordes_seleccionada = None
historial_progresiones = []
futuro_progresiones = []
ritmo_actual_progresion = []
current_piano_roll_instance = None
botones_instrumento_acordes = []
boton_instr_acordes_seleccionado = None
botones_instrumento_melodia = []
boton_instr_melodia_seleccionado = None
transposicion_actual_st = 0
label_transposicion_var = None
feedback_status_label = None
feedback_status_label_var = None
_feedback_after_id = None
COLOR_BORDE_SELECCIONADO = "#003366"
ANCHO_BORDE_SELECCIONADO = 1.5
RELIEF_SELECCIONADO = tk.SOLID

try:
    instrumento_seleccionado_acordes = instrument.Piano()
    instrumento_seleccionado_melodia = instrument.Piano()
except Exception as e_init:
    print(f"Error inicializando instrumentos music21: {e_init}")
    instrumento_seleccionado_acordes = "Piano"
    instrumento_seleccionado_melodia = "Piano"

ventana_principal = None
entrada_prompt_texto = None
combo_cantidad = None
label_acordes_generados_var = None
label_ruta_guardado_var = None
frame_piano_roll_display = None
ritmo_seleccionado_label_var = None
background_label = None
photo_image = None
ultima_melodia_generada_path = None
ultimo_midi_acordes_path = None
label_bpm_var = None
bpm_control_var = None
bpm_frame = None
show_alternos = None
spin_bpm = None

RUTA_BASE_PROYECTO = os.path.dirname(os.path.abspath(__file__))
CARPETA_MIDI_EXPORTADO = os.path.join(RUTA_BASE_PROYECTO, "MIDI_EXPORTADO")
CARPETA_TEMP_PLAYBACK = os.path.join(RUTA_BASE_PROYECTO, "temp")

def resource_path(relative_path):
    """ Obtiene la ruta absoluta a un recurso, funciona para desarrollo y para el bundle de PyInstaller. """
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # base_path será la ruta del script en desarrollo (donde está main.py)
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# --- Funciones de Ayuda y Lógica ---

def convertir_progresion_a_tuplas_para_feedback(acordes_lista_o_str):
    prog_tuplas = []
    if not acordes_lista_o_str:
        return prog_tuplas
    for ac in acordes_lista_o_str:
        if isinstance(ac, list):
            prog_tuplas.append(tuple(sorted(ac)))
        elif isinstance(ac, str) and ac == "0":
            prog_tuplas.append("0")
        else:
            print(f"Advertencia: Elemento de acorde no esperado para feedback: {ac}. Tratado como '0'.")
            prog_tuplas.append("0")
    return prog_tuplas

def accion_feedback(es_buena):
    global historial_progresiones, label_ruta_guardado_var
    global feedback_status_label, feedback_status_label_var, _feedback_after_id
    global entrada_prompt_texto

    if _feedback_after_id:
        if feedback_status_label:
             feedback_status_label.after_cancel(_feedback_after_id)
        _feedback_after_id = None

    if not historial_progresiones:
        if feedback_status_label and feedback_status_label_var:
            feedback_status_label_var.set("Genera una progresión primero.")
            feedback_status_label.config(fg="#FFA500")
            _feedback_after_id = feedback_status_label.after(2500, lambda: feedback_status_label_var.set(""))
        else:
            messagebox.showinfo("Feedback", "Primero genera una progresión para dar tu opinión.")
        return

    raiz_actual_hist, modo_actual_hist, estilo_actual_hist, acordes_actuales_listas_hist, ritmo_asociado_hist, _melodia_hist = historial_progresiones[-1]

    if not acordes_actuales_listas_hist or not estilo_actual_hist or not raiz_actual_hist or not modo_actual_hist:
        if feedback_status_label and feedback_status_label_var:
            feedback_status_label_var.set("Error: Faltan datos de progresión.")
            feedback_status_label.config(fg="#DC3545")
            _feedback_after_id = feedback_status_label.after(3000, lambda: feedback_status_label_var.set(""))
        else:
            messagebox.showerror("Feedback Error", "No hay suficiente información de la progresión actual.")
        return

    progresion_para_feedback_tuplas = convertir_progresion_a_tuplas_para_feedback(acordes_actuales_listas_hist)

    if not progresion_para_feedback_tuplas:
        if feedback_status_label and feedback_status_label_var:
            feedback_status_label_var.set("Error: Progresión no procesable.")
            feedback_status_label.config(fg="#DC3545")
            _feedback_after_id = feedback_status_label.after(3000, lambda: feedback_status_label_var.set(""))
        else:
            messagebox.showerror("Feedback Error", "La progresión actual está vacía o en un formato no procesable.")
        return

    clave_tonalidad_feedback = f"{raiz_actual_hist.lower()} {modo_actual_hist.lower()}"

    exito_refuerzo = reforzar_progresion_con_feedback(
        estilo_actual_hist,
        clave_tonalidad_feedback,
        progresion_para_feedback_tuplas,
        ritmo_asociado_hist,
        es_buena
    )

    if feedback_status_label and feedback_status_label_var:
        if exito_refuerzo:
            if es_buena:
                display_message = "Mejorando aprendizaje..."
                text_color = "#28A745"
            else:
                display_message = "Feedback 👎 registrado."
                text_color = COLOR_FG_TEXT_SECUNDARIO

            feedback_status_label_var.set(display_message)
            feedback_status_label.config(fg=text_color)
            _feedback_after_id = feedback_status_label.after(2500, lambda: feedback_status_label_var.set(""))

            if label_ruta_guardado_var:
                log_msg = "Aprendizaje mejorado con 👍." if es_buena else "Feedback 👎 procesado."
                label_ruta_guardado_var.set(log_msg)

            if not es_buena:
                print("INFO: Feedback negativo recibido, generando nueva progresión.")
                ventana_principal.after(300, accion_generar_desde_prompt)

        else:
            feedback_status_label_var.set("Error al guardar feedback.")
            feedback_status_label.config(fg="#DC3545")
            _feedback_after_id = feedback_status_label.after(3000, lambda: feedback_status_label_var.set(""))

            if label_ruta_guardado_var:
                label_ruta_guardado_var.set("Error al procesar/guardar feedback.")
    else:
        if exito_refuerzo:
            feedback_msg_mb = "¡Gracias! Aprendiendo de tu 👍." if es_buena else "Feedback 👎 registrado. Intentaremos mejorar."
            messagebox.showinfo("Feedback Enviado", feedback_msg_mb)
            if not es_buena:
                 ventana_principal.after(300, accion_generar_desde_prompt)
        else:
            messagebox.showerror("Feedback Error", "Hubo un problema al procesar tu feedback.")


def cambiar_bpm_dialogo():
    global bpm_actual, label_bpm_var, bpm_control_var
    nuevo_bpm_dialog = simpledialog.askinteger("Ajustar BPM",
        "Introduce el BPM deseado (20–300):",
        initialvalue=bpm_actual, minvalue=20, maxvalue=300)
    if nuevo_bpm_dialog is not None:
        bpm_actual = nuevo_bpm_dialog
        if label_bpm_var:
            label_bpm_var.set(f"BPM: {bpm_actual}")
        if bpm_control_var:
            bpm_control_var.set(bpm_actual)

def actualizar_cantidad_acordes(event=None):
    global cantidad_acordes_seleccionada
    if combo_cantidad:
        seleccion = combo_cantidad.get()
        if seleccion == "Sin límite":
            cantidad_acordes_seleccionada = None
        else:
            try:
                cantidad_acordes_seleccionada = int(seleccion)
            except ValueError:
                cantidad_acordes_seleccionada = None
    else:
        cantidad_acordes_seleccionada = None

def actualizar_display_transposicion():
    global transposicion_actual_st, label_transposicion_var
    if label_transposicion_var:
        texto_transposicion = f"{transposicion_actual_st:+} st" if transposicion_actual_st != 0 else "0 st"
        label_transposicion_var.set(texto_transposicion)

def seleccionar_instrumento_para_acordes(ClaseInstrumentoMusic21, boton_presionado):
    global instrumento_seleccionado_acordes, boton_instr_acordes_seleccionado
    try:
        instrumento_seleccionado_acordes = ClaseInstrumentoMusic21()
        if boton_instr_acordes_seleccionado:
            boton_instr_acordes_seleccionado.config(relief=tk.FLAT, bd=0, highlightthickness=0)
        boton_instr_acordes_seleccionado = boton_presionado
        boton_instr_acordes_seleccionado.config(
            relief=RELIEF_SELECCIONADO,
            bd=int(ANCHO_BORDE_SELECCIONADO),
            highlightbackground=COLOR_BORDE_SELECCIONADO,
            highlightcolor=COLOR_BORDE_SELECCIONADO,
            highlightthickness=int(ANCHO_BORDE_SELECCIONADO)
        )
    except Exception as e:
        print(f"Error seleccionando instrumento para acordes: {e}")
        instrumento_seleccionado_acordes = instrument.Piano()
        if boton_instr_acordes_seleccionado:
            boton_instr_acordes_seleccionado.config(relief=tk.FLAT, bd=0, highlightthickness=0)
            boton_instr_acordes_seleccionado = None

def seleccionar_instrumento_para_melodia(ClaseInstrumentoMusic21, boton_presionado):
    global instrumento_seleccionado_melodia, boton_instr_melodia_seleccionado
    try:
        instrumento_seleccionado_melodia = ClaseInstrumentoMusic21()
        if boton_instr_melodia_seleccionado:
            boton_instr_melodia_seleccionado.config(relief=tk.FLAT, bd=0, highlightthickness=0)
        boton_instr_melodia_seleccionado = boton_presionado
        boton_instr_melodia_seleccionado.config(
            relief=RELIEF_SELECCIONADO,
            bd=int(ANCHO_BORDE_SELECCIONADO),
            highlightbackground=COLOR_BORDE_SELECCIONADO,
            highlightcolor=COLOR_BORDE_SELECCIONADO,
            highlightthickness=int(ANCHO_BORDE_SELECCIONADO)
        )
    except Exception as e:
        print(f"Error seleccionando instrumento para melodía: {e}")
        instrumento_seleccionado_melodia = instrument.Piano()
        if boton_instr_melodia_seleccionado:
            boton_instr_melodia_seleccionado.config(relief=tk.FLAT, bd=0, highlightthickness=0)
            boton_instr_melodia_seleccionado = None


def mostrar_progresion_en_salida(acordes_a_mostrar, texto_informativo, ritmo_para_piano_roll=None, melodia_para_piano_roll=None):
    global label_acordes_generados_var, ritmo_seleccionado_label_var
    global frame_piano_roll_display, current_piano_roll_instance

    if label_acordes_generados_var:
        if acordes_a_mostrar and any(a != "0" and a != "N/A" for a in acordes_a_mostrar):
            ac_display_strings = []
            for ac_item in acordes_a_mostrar:
                if isinstance(ac_item, list):
                    display_str = f"[{', '.join(ac_item[:3])}"
                    if len(ac_item) > 3: display_str += ",..."
                    display_str += "]"
                    ac_display_strings.append(display_str)
                else:
                    ac_display_strings.append(str(ac_item))
            label_acordes_generados_var.set("🧾 Acordes: " + " - ".join(ac_display_strings))
        else:
            label_acordes_generados_var.set("🧾 Acordes: (vacío o no generados)")

    ritmo_final_para_display = ritmo_para_piano_roll if ritmo_para_piano_roll is not None else []

    if ritmo_seleccionado_label_var:
        if ritmo_final_para_display:
            ritmo_display_list = [round(float(r_val), 2) for r_val in ritmo_final_para_display]
            ritmo_texto_completo = f"{ritmo_display_list}"
            max_len_ritmo_texto = 40
            ritmo_texto_visible = (ritmo_texto_completo[:max_len_ritmo_texto - 3] + "...") if len(ritmo_texto_completo) > max_len_ritmo_texto else ritmo_texto_completo
            ritmo_seleccionado_label_var.set(f"Ritmo Usado: {ritmo_texto_visible}")
        else:
            ritmo_seleccionado_label_var.set("Ritmo Usado: N/A")

    if frame_piano_roll_display:
        if current_piano_roll_instance:
            if hasattr(current_piano_roll_instance, 'is_playing') and current_piano_roll_instance.is_playing:
                current_piano_roll_instance.detener_cursor_reproduccion()
            for widget in frame_piano_roll_display.winfo_children():
                 widget.destroy()
            current_piano_roll_instance = None

        base_px_por_pulso = 60
        acordes_validos_para_roll = acordes_a_mostrar if acordes_a_mostrar and any(ac_valido != "0" and ac_valido != "N/A" for ac_valido in acordes_a_mostrar) else []

        try:
            current_piano_roll_instance = PianoRoll(frame_piano_roll_display,
                                                acordes_validos_para_roll,
                                                ritmo_final_para_display,
                                                melodia_data=melodia_para_piano_roll,
                                                base_pixeles_por_pulso=base_px_por_pulso)
            current_piano_roll_instance.pack(fill="both", expand=True)
        except Exception as e_roll:
            print(f"Error creando PianoRoll: {e_roll}")
            tk.Label(frame_piano_roll_display, text=f"⚠️ Error Piano Roll:\n{e_roll}",
                     bg=COLOR_PIANO_ROLL_BG, fg="#FF0000", justify=tk.LEFT).pack(padx=10, pady=10, expand=True)


def detener_reproduccion_actual():
    global current_piano_roll_instance, label_ruta_guardado_var
    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
    if current_piano_roll_instance:
        current_piano_roll_instance.detener_cursor_reproduccion()
    if label_ruta_guardado_var: label_ruta_guardado_var.set("⏹️ Reproducción detenida.")

def calcular_duracion_total_ms(ritmo_progresion_pulsos, bpm_val=120):
    if not ritmo_progresion_pulsos: return 0
    segundos_por_pulso = 60.0 / bpm_val
    try:
        duracion_total_pulsos = sum(float(d_val) for d_val in ritmo_progresion_pulsos)
    except (ValueError, TypeError): return 0
    return duracion_total_pulsos * segundos_por_pulso * 1000


def accion_generar_desde_prompt(usar_markov_override=False):
    global ultima_raiz, ultimo_modo, ultimo_estilo_generado, historial_progresiones, futuro_progresiones
    global ritmo_actual_progresion, current_piano_roll_instance
    global label_ruta_guardado_var, label_acordes_generados_var, cantidad_acordes_seleccionada
    global entrada_prompt_texto, transposicion_actual_st
    global bpm_actual, bpm_control_var, label_bpm_var, ventana_principal

    prompt_usuario = entrada_prompt_texto.get()
    if not prompt_usuario:
        if label_acordes_generados_var: label_acordes_generados_var.set("🧾 Acordes: Por favor, escribe un prompt.");
        if ventana_principal: ventana_principal.focus_set()
        return

    # NO leer BPM del spinbox aquí todavía, se hará después de determinar el género

    transposicion_actual_st = 0
    actualizar_display_transposicion()

    # 1. Detección inicial de estilo y tonalidad explícitos
    estilo_explicito = detectar_estilo(prompt_usuario)
    raiz_explicita, modo_explicito = extraer_tonalidad(prompt_usuario, estilo_detectado_param=estilo_explicito)

    # 2. Detección de sentimiento
    sentimiento_detectado = detectar_sentimiento_en_prompt(prompt_usuario)
    print(f"INFO (Prompt): Estilo explícito: '{estilo_explicito}', Raíz explícita: '{raiz_explicita}', Modo explícito: '{modo_explicito}', Sentimiento: '{sentimiento_detectado}'")

    # 3. Inferencia de parámetros basada en sentimiento y explícitos
    generos_entrenados_reales = {
        g for g in INFO_GENERO.keys()
        if g != "patrones_ritmicos" and isinstance(INFO_GENERO.get(g), dict) and
        any(INFO_GENERO[g].get(k) for k in INFO_GENERO[g] if k != "patrones_ritmicos")
    }
    if not generos_entrenados_reales and INFO_GENERO: # Fallback si la estructura es más simple
        generos_entrenados_reales = {g for g in INFO_GENERO.keys() if g != "patrones_ritmicos"}


    estilo_final, raiz_final, modo_final = inferir_parametros_desde_sentimiento(
        sentimiento_detectado,
        estilo_explicito,
        raiz_explicita,
        modo_explicito,
        generos_entrenados_reales
    )
    print(f"INFO (Inferencia): Estilo final: '{estilo_final}', Raíz final: '{raiz_final}', Modo final: '{modo_final}'")

    # 4. Verificación de género final y aplicación de BPM por género
    if not estilo_final or estilo_final == "normal" or estilo_final not in INFO_GENERO or not INFO_GENERO.get(estilo_final):
        nombre_genero_solicitado = estilo_explicito if estilo_explicito and estilo_explicito != "normal" else (prompt_usuario.split()[0] if prompt_usuario else 'desconocido')
        mensaje_dialogo = f"No encontré el género musical '{nombre_genero_solicitado}' o no tengo datos suficientes para él.\nIntenta con otro género o sé más específico."
        if sentimiento_detectado and (not estilo_explicito or estilo_explicito == "normal"):
             mensaje_dialogo = f"No pude encontrar un género adecuado para '{sentimiento_detectado}' con los datos actuales.\nPrueba especificando un género."

        mostrar_dialogo_bienvenida(ventana_principal,
                                   titulo="Género No Encontrado o Sin Datos",
                                   mensaje_personalizado=mensaje_dialogo,
                                   mostrar_saludo_inicial=False,
                                   color_mensaje=COLOR_DIALOGO_ERROR_FG)
        if label_acordes_generados_var: label_acordes_generados_var.set(f"🧾 Acordes: (género '{nombre_genero_solicitado}' no procesable)")
        if label_ruta_guardado_var: label_ruta_guardado_var.set("📁 (Generación cancelada)")
        if ventana_principal: ventana_principal.focus_set()
        return
    else: # Género final es válido, aplicar BPM por género
        bpm_min, bpm_max, bpm_sugerido = MAPEO_GENERO_BPM.get(estilo_final, MAPEO_GENERO_BPM["normal"])
        # Por ahora, usaremos el bpm_sugerido. Podríamos elegir aleatorio en el rango.
        bpm_actual = bpm_sugerido
        if bpm_control_var: bpm_control_var.set(bpm_actual)
        if label_bpm_var: label_bpm_var.set(f"BPM: {bpm_actual}")
        print(f"INFO (BPM por Género): BPM establecido a {bpm_actual} para el género '{estilo_final}'.")


    if not raiz_final: raiz_final = "C"
    if not modo_final: modo_final = "major"

    ultima_raiz = raiz_final
    ultimo_modo = modo_final
    ultimo_estilo_generado = estilo_final

    # 5. Generación de acordes
    acordes_generados_lista, ritmo_obtenido = generar_progresion_acordes_smart(
        raiz_final,
        modo_final,
        estilo_final,
        cantidad_acordes_seleccionada,
        usar_markov_directamente=usar_markov_override
    )

    if not acordes_generados_lista or not ritmo_obtenido:
        mensaje_error = f"⚠️ No se pudo generar una progresión para '{prompt_usuario}' (Estilo: {estilo_final}, Tonalidad: {raiz_final} {modo_final})."
        num_fallback_display = cantidad_acordes_seleccionada if cantidad_acordes_seleccionada is not None else 4
        mostrar_progresion_en_salida(["N/A"] * num_fallback_display, mensaje_error, [], melodia_para_piano_roll=[])
        if label_acordes_generados_var: label_acordes_generados_var.set(f"🧾 Acordes: {mensaje_error}");
        if label_ruta_guardado_var: label_ruta_guardado_var.set("📁 (Generación fallida)");
        if ventana_principal: ventana_principal.focus_set()
        return

    ritmo_actual_progresion = [float(r) if isinstance(r, (int, float, str)) else 1.0 for r in ritmo_obtenido]

    if len(ritmo_actual_progresion) != len(acordes_generados_lista):
        print(f"ADVERTENCIA: Discrepancia de longitud entre acordes ({len(acordes_generados_lista)}) y ritmo ({len(ritmo_actual_progresion)}). Ajustando ritmo.")
        if len(ritmo_actual_progresion) < len(acordes_generados_lista):
            ritmo_actual_progresion.extend([1.0] * (len(acordes_generados_lista) - len(ritmo_actual_progresion)))
        else:
            ritmo_actual_progresion = ritmo_actual_progresion[:len(acordes_generados_lista)]

    historial_progresiones.append((raiz_final, modo_final, estilo_final, acordes_generados_lista, ritmo_actual_progresion.copy(), []))
    futuro_progresiones.clear()

    info_display_prompt = f"'{prompt_usuario}' (Estilo: {estilo_final}, Tonalidad: {raiz_final} {modo_final}, Sentimiento: {sentimiento_detectado if sentimiento_detectado else 'N/A'})"
    mostrar_progresion_en_salida(acordes_generados_lista,
                             f"🎶 Progresión para {info_display_prompt}:",
                             ritmo_actual_progresion,
                             melodia_para_piano_roll=[])
    if label_ruta_guardado_var: label_ruta_guardado_var.set("📁 (Progresión no exportada)")

    if ventana_principal:
        ventana_principal.focus_set()


def accion_generar_melodia():
    global bpm_actual, bpm_control_var, label_bpm_var
    global ultima_melodia_generada_path, label_ruta_guardado_var
    global historial_progresiones, futuro_progresiones, current_piano_roll_instance

    # El BPM ya debería estar actualizado por accion_generar_desde_prompt
    # o por el usuario. Si se quiere re-evaluar BPM por género aquí, se podría.
    # Por ahora, se usa el bpm_actual que ya existe.
    if bpm_control_var: # Asegurar que la UI refleje el bpm_actual
        if bpm_actual != bpm_control_var.get():
             bpm_control_var.set(bpm_actual)
        if label_bpm_var:
             label_bpm_var.set(f"BPM: {bpm_actual}")


    if not historial_progresiones:
        if feedback_status_label_var and feedback_status_label:
            feedback_status_label_var.set("Genera acordes primero.")
            feedback_status_label.config(fg="#FFA500")
            global _feedback_after_id
            if _feedback_after_id: feedback_status_label.after_cancel(_feedback_after_id)
            _feedback_after_id = feedback_status_label.after(2500, lambda: feedback_status_label_var.set(""))
        return

    raiz_prog_mel, modo_prog_mel, estilo_prog_mel, acordes_hist_mel, ritmo_hist_mel, _ = historial_progresiones[-1]

    raiz_para_gen_mel = raiz_prog_mel if raiz_prog_mel else ultima_raiz
    modo_para_gen_mel = modo_prog_mel if modo_prog_mel else ultimo_modo
    if not raiz_para_gen_mel or not modo_para_gen_mel: raiz_para_gen_mel, modo_para_gen_mel = "C", "major"


    melodia_generada_notas_durs = generar_melodia_sobre_acordes(
        acordes_hist_mel,
        ritmo_hist_mel,
        raiz_para_gen_mel,
        modo_para_gen_mel,
        bpm=bpm_actual
    )

    if not melodia_generada_notas_durs:
        if label_ruta_guardado_var: label_ruta_guardado_var.set("📁 Falló generación de melodía"); return

    historial_progresiones[-1] = (
        raiz_prog_mel,
        modo_prog_mel,
        estilo_prog_mel,
        acordes_hist_mel,
        ritmo_hist_mel,
        melodia_generada_notas_durs
    )
    futuro_progresiones.clear()

    if current_piano_roll_instance:
        current_piano_roll_instance.actualizar_datos(acordes_hist_mel, ritmo_hist_mel, melodia_generada_notas_durs)

    path_melodia_exportada = exportar_melodia_a_midi_individual(melodia_generada_notas_durs, for_playback=False)
    if path_melodia_exportada:
        ultima_melodia_generada_path = path_melodia_exportada
        if label_ruta_guardado_var: label_ruta_guardado_var.set(f"🎶 Melodía Guardada: {os.path.basename(path_melodia_exportada)}")
    else:
        if label_ruta_guardado_var: label_ruta_guardado_var.set("📁 Falló exportación de melodía")


def accion_nuevo_patron_ritmico():
    global ritmo_actual_progresion, historial_progresiones, futuro_progresiones, label_ruta_guardado_var

    if not historial_progresiones:
        messagebox.showinfo("Ritmo", "Genera una progresión de acordes primero.")
        return

    raiz_act, modo_act, estilo_act, acordes_actuales_hist, ritmo_viejo, melodia_actual = historial_progresiones[-1]

    nuevo_ritmo_raw = None
    try:
        from generador_acordes import cargar_patron_ritmico_acordes
        nuevo_ritmo_raw = cargar_patron_ritmico_acordes(estilo_act, len(acordes_actuales_hist))
    except ImportError:
        print("ADVERTENCIA: 'cargar_patron_ritmico_acordes' no encontrada. Usando ritmo por defecto.")
    except Exception as e_cargar_ritmo:
        print(f"Error al cargar patrón rítmico: {e_cargar_ritmo}. Usando ritmo por defecto.")

    if nuevo_ritmo_raw is None:
        nuevo_ritmo_raw = [1.0] * len(acordes_actuales_hist) if acordes_actuales_hist else []


    nuevo_ritmo_float = [float(r_val) for r_val in nuevo_ritmo_raw] if nuevo_ritmo_raw else ritmo_actual_progresion.copy()

    if acordes_actuales_hist:
        if len(nuevo_ritmo_float) != len(acordes_actuales_hist):
            print(f"ADVERTENCIA: Discrepancia ritmo ({len(nuevo_ritmo_float)}) y acordes ({len(acordes_actuales_hist)}). Ajustando ritmo.")
            if len(nuevo_ritmo_float) < len(acordes_actuales_hist):
                nuevo_ritmo_float.extend([1.0] * (len(acordes_actuales_hist) - len(nuevo_ritmo_float)))
            else:
                nuevo_ritmo_float = nuevo_ritmo_float[:len(acordes_actuales_hist)]
    elif not nuevo_ritmo_float:
        nuevo_ritmo_float = []

    if nuevo_ritmo_float and nuevo_ritmo_float != ritmo_actual_progresion:
        ritmo_actual_progresion = nuevo_ritmo_float

        historial_progresiones.append((
            raiz_act, modo_act, estilo_act,
            acordes_actuales_hist, ritmo_actual_progresion.copy(), melodia_actual
        ))
        futuro_progresiones.clear()

        mostrar_progresion_en_salida(
            acordes_actuales_hist, "🎶 Ritmo actualizado:",
            ritmo_actual_progresion, melodia_actual
        )
        if label_ruta_guardado_var: label_ruta_guardado_var.set("📁 (Ritmo modificado, progresión no exportada)")
    else:
        mostrar_progresion_en_salida(
            acordes_actuales_hist, "Mismo ritmo o sin cambios.",
            ritmo_actual_progresion, melodia_actual
        )


def accion_subir_semitono():
    global historial_progresiones, futuro_progresiones, label_ruta_guardado_var, transposicion_actual_st

    if historial_progresiones:
        raiz, modo, estilo, acordes_originales, ritmo_asociado, melodia_original = historial_progresiones[-1]

        acordes_transpuestos, melodia_transpuesta = transponer_progresion(acordes_originales, 1, melodia_original)

        transposicion_actual_st += 1
        actualizar_display_transposicion()

        historial_progresiones.append((raiz, modo, estilo, acordes_transpuestos, ritmo_asociado, melodia_transpuesta))
        futuro_progresiones.clear()

        mostrar_progresion_en_salida(acordes_transpuestos, "🔺 Transpuesto:", ritmo_asociado, melodia_transpuesta)
        if label_ruta_guardado_var: label_ruta_guardado_var.set("📁 (Modificado, no exportado)")
    else:
        if label_ruta_guardado_var: label_ruta_guardado_var.set("📁 No hay progresión para transponer.")

def accion_bajar_semitono():
    global historial_progresiones, futuro_progresiones, label_ruta_guardado_var, transposicion_actual_st

    if historial_progresiones:
        raiz, modo, estilo, acordes_originales, ritmo_asociado, melodia_original = historial_progresiones[-1]

        acordes_transpuestos, melodia_transpuesta = transponer_progresion(acordes_originales, -1, melodia_original)

        transposicion_actual_st -= 1
        actualizar_display_transposicion()

        historial_progresiones.append((raiz, modo, estilo, acordes_transpuestos, ritmo_asociado, melodia_transpuesta))
        futuro_progresiones.clear()

        mostrar_progresion_en_salida(acordes_transpuestos, "🔻 Transpuesto:", ritmo_asociado, melodia_transpuesta)
        if label_ruta_guardado_var: label_ruta_guardado_var.set("📁 (Modificado, no exportado)")
    else:
        if label_ruta_guardado_var: label_ruta_guardado_var.set("📁 No hay progresión para transponer.")


def accion_deshacer(event=None):
    global historial_progresiones, futuro_progresiones, ritmo_actual_progresion, transposicion_actual_st
    global label_ruta_guardado_var, label_acordes_generados_var, ritmo_seleccionado_label_var

    if len(historial_progresiones) >= 2:
        paso_actual_deshecho = historial_progresiones.pop()
        futuro_progresiones.append(paso_actual_deshecho)

        raiz_prev, modo_prev, estilo_prev, acordes_prev, ritmo_prev, melodia_prev = historial_progresiones[-1]

        ritmo_actual_progresion = ritmo_prev.copy() if ritmo_prev else []
        transposicion_actual_st = 0
        actualizar_display_transposicion()

        mostrar_progresion_en_salida(acordes_prev, "↩ Deshacer.", ritmo_prev, melodia_prev)

        if label_ruta_guardado_var: label_ruta_guardado_var.set("📁 (Deshacer realizado)")
    elif len(historial_progresiones) == 1:
        paso_actual_deshecho = historial_progresiones.pop()
        futuro_progresiones.append(paso_actual_deshecho)
        ritmo_actual_progresion = []
        transposicion_actual_st = 0
        actualizar_display_transposicion()
        mostrar_progresion_en_salida([], "↩ Deshacer. Lienzo vacío.", [], [])
        if label_ruta_guardado_var: label_ruta_guardado_var.set("📁 (Lienzo vacío)")
        if label_acordes_generados_var: label_acordes_generados_var.set("🧾 Acordes: (vacío)")
        if ritmo_seleccionado_label_var: ritmo_seleccionado_label_var.set("Ritmo Usado: N/A")

    else:
        if feedback_status_label and feedback_status_label_var:
            feedback_status_label_var.set("Nada que deshacer.")
            feedback_status_label.config(fg=COLOR_FG_TEXT_SECUNDARIO)
            global _feedback_after_id
            if _feedback_after_id: feedback_status_label.after_cancel(_feedback_after_id)
            _feedback_after_id = feedback_status_label.after(2000, lambda: feedback_status_label_var.set(""))
        else:
            messagebox.showinfo("Deshacer", "No hay nada que deshacer.")


def accion_rehacer(event=None):
    global historial_progresiones, futuro_progresiones, ritmo_actual_progresion, transposicion_actual_st
    global label_ruta_guardado_var

    if futuro_progresiones:
        paso_a_rehacer = futuro_progresiones.pop()
        historial_progresiones.append(paso_a_rehacer)

        raiz_rehecha, modo_rehecho, estilo_rehecho, acordes_rehechos, ritmo_rehecho, melodia_rehecha = paso_a_rehacer

        ritmo_actual_progresion = ritmo_rehecho.copy() if ritmo_rehecho else []
        transposicion_actual_st = 0
        actualizar_display_transposicion()

        mostrar_progresion_en_salida(acordes_rehechos, "↷ Rehacer.", ritmo_rehecho, melodia_rehecha)
        if label_ruta_guardado_var: label_ruta_guardado_var.set("📁 (Rehacer realizado)")
    else:
        if feedback_status_label and feedback_status_label_var:
            feedback_status_label_var.set("Nada que rehacer.")
            feedback_status_label.config(fg=COLOR_FG_TEXT_SECUNDARIO)
            global _feedback_after_id
            if _feedback_after_id: feedback_status_label.after_cancel(_feedback_after_id)
            _feedback_after_id = feedback_status_label.after(2000, lambda: feedback_status_label_var.set(""))
        else:
            messagebox.showinfo("Rehacer", "No hay nada que rehacer.")

# --- Funciones de Exportación y Reproducción MIDI ---

def _export_midi_base(stream_obj_export, base_filename_prefix, for_playback=False, raiz_suffix=None, modo_suffix=None):
    os.makedirs(CARPETA_MIDI_EXPORTADO, exist_ok=True)
    if for_playback:
        os.makedirs(CARPETA_TEMP_PLAYBACK, exist_ok=True)

    final_folder_path = CARPETA_TEMP_PLAYBACK if for_playback else CARPETA_MIDI_EXPORTADO

    filename = f"{base_filename_prefix}.mid"
    final_path = os.path.join(final_folder_path, filename)

    try:
        mf = midi.translate.streamToMidiFile(stream_obj_export)
        mf.open(final_path, "wb")
        mf.write()
        mf.close()

        if not for_playback and label_ruta_guardado_var:
            pass

        return final_path
    except Exception as e_export:
        print(f"Error exportando MIDI a {final_path}: {e_export}")
        if not for_playback and label_ruta_guardado_var:
            label_ruta_guardado_var.set(f"📁 Error exportando: {filename}")
        return None

def exportar_acordes_a_midi_individual(for_playback=False):
    global ultimo_midi_acordes_path, instrumento_seleccionado_acordes, historial_progresiones, label_ruta_guardado_var, bpm_actual

    if not historial_progresiones:
        if label_ruta_guardado_var and not for_playback:
            label_ruta_guardado_var.set("📁 No hay acordes para exportar.")
        return None

    raiz_actual_hist, modo_actual_hist, _estilo, acordes_a_exportar, ritmo_de_acordes_hist, _melodia_hist = historial_progresiones[-1]

    s = stream.Stream()
    s.insert(0, MetronomeMark(number=bpm_actual))
    s.append(
        instrumento_seleccionado_acordes
        if isinstance(instrumento_seleccionado_acordes, instrument.Instrument)
        else instrument.Piano()
    )

    current_offset = 0.0
    ritmo_ajustado_float = [float(r_val) for r_val in ritmo_de_acordes_hist] if ritmo_de_acordes_hist else [1.0] * len(acordes_a_exportar)

    for i, ac_data in enumerate(acordes_a_exportar):
        duracion_elemento = ritmo_ajustado_float[i % len(ritmo_ajustado_float)]
        elemento_musical = None
        try:
            if isinstance(ac_data, str) and ac_data in ("0", "N/A"):
                elemento_musical = note.Rest(quarterLength=duracion_elemento)
            elif isinstance(ac_data, list):
                notas_con_octava_final = []
                for n_str in ac_data:
                    if re.search(r"\d", n_str):
                        notas_con_octava_final.append(n_str)
                    else:
                        notas_con_octava_final.append(f"{n_str}4")
                elemento_musical = chord.Chord(notas_con_octava_final, quarterLength=duracion_elemento)
        except Exception as e_chord_create:
            print(f"Error creando elemento musical para MIDI desde '{ac_data}': {e_chord_create}. Insertando silencio.")
            elemento_musical = note.Rest(quarterLength=duracion_elemento)

        if elemento_musical:
            elemento_musical.offset = current_offset
            s.append(elemento_musical)
            current_offset += duracion_elemento

    path_guardado = _export_midi_base(s, "acordes", for_playback, raiz_actual_hist, modo_actual_hist)
    if path_guardado and not for_playback:
        ultimo_midi_acordes_path = path_guardado
    return path_guardado


def exportar_melodia_a_midi_individual(melodia_notas_y_duraciones, for_playback=False):
    global instrumento_seleccionado_melodia, ultima_melodia_generada_path, bpm_actual

    if not melodia_notas_y_duraciones: return None

    s = stream.Stream()
    s.insert(0, MetronomeMark(number=bpm_actual))
    s.append(
        instrumento_seleccionado_melodia
        if isinstance(instrumento_seleccionado_melodia, instrument.Instrument)
        else instrument.Piano()
    )

    current_offset = 0.0
    for nombre_nota_mel, duracion_nota_mel_val in melodia_notas_y_duraciones:
        elemento_melodico = None
        try:
            duracion_float = float(duracion_nota_mel_val)
            if nombre_nota_mel == "0":
                elemento_melodico = note.Rest(quarterLength=duracion_float)
            else:
                nota_con_octava_mel = f"{nombre_nota_mel}4" if not re.search(r'\d$', nombre_nota_mel) else nombre_nota_mel
                elemento_melodico = note.Note(nota_con_octava_mel, quarterLength=duracion_float)

            if elemento_melodico:
                elemento_melodico.offset = current_offset
                s.append(elemento_melodico)
                current_offset += duracion_float
        except Exception as e_note_create:
            print(f"Error creando nota de melodía para MIDI desde '{nombre_nota_mel}': {e_note_create}")
            continue

    path_guardado = _export_midi_base(s, "melodia", for_playback)
    if path_guardado and not for_playback:
        ultima_melodia_generada_path = path_guardado
    return path_guardado


def reproducir_midi_acordes():
    global bpm_actual, bpm_control_var, label_bpm_var, label_ruta_guardado_var, ritmo_actual_progresion, current_piano_roll_instance

    if bpm_control_var:
        try:
            valor_bpm_spinbox = int(bpm_control_var.get())
            if 20 <= valor_bpm_spinbox <= 300:
                bpm_actual = valor_bpm_spinbox
                if label_bpm_var: label_bpm_var.set(f"BPM: {bpm_actual}")
            else:
                bpm_control_var.set(bpm_actual)
        except tk.TclError: pass
        except ValueError:
            if bpm_control_var: bpm_control_var.set(bpm_actual)
        except Exception as e_bpm_get:
            print(f"Error obteniendo BPM del spinbox: {e_bpm_get}")

    path_temporal_acordes = exportar_acordes_a_midi_individual(for_playback=True)

    if not path_temporal_acordes or not os.path.exists(path_temporal_acordes):
        if label_ruta_guardado_var: label_ruta_guardado_var.set("📁 Sin acordes para reprod."); return

    try:
        if not pygame.mixer.get_init(): pygame.mixer.init()
        pygame.mixer.music.stop()
        if current_piano_roll_instance: current_piano_roll_instance.detener_cursor_reproduccion()

        pygame.mixer.music.load(path_temporal_acordes)
        pygame.mixer.music.play(loops=-1)

        if current_piano_roll_instance and ritmo_actual_progresion:
            try:
                ritmo_valido_para_dur = [float(d_val) for d_val in ritmo_actual_progresion]
                duracion_total_ms_calc = calcular_duracion_total_ms(ritmo_valido_para_dur, bpm_actual)
                if duracion_total_ms_calc > 0:
                    current_piano_roll_instance.iniciar_cursor_reproduccion(duracion_total_ms_calc)
            except (ValueError, TypeError) as e_dur_calc:
                 print(f"Error calculando duración para cursor: {e_dur_calc}")

        if label_ruta_guardado_var: label_ruta_guardado_var.set(f"▶️ Reprod. Acordes (Bucle): {os.path.basename(path_temporal_acordes)} (BPM: {bpm_actual})")
    except Exception as e_play:
        print(f"Error reproducción acordes: {e_play}")
        if label_ruta_guardado_var: label_ruta_guardado_var.set(f"📁 Error reproducción acordes: {e_play}")


def reproducir_midi_melodia():
    global historial_progresiones, bpm_actual, bpm_control_var, label_bpm_var, instrumento_seleccionado_melodia, label_ruta_guardado_var
    global current_piano_roll_instance

    if bpm_control_var:
        try:
            valor_bpm_spinbox = int(bpm_control_var.get())
            if 20 <= valor_bpm_spinbox <= 300:
                bpm_actual = valor_bpm_spinbox
                if label_bpm_var: label_bpm_var.set(f"BPM: {bpm_actual}")
            else:
                bpm_control_var.set(bpm_actual)
        except tk.TclError: pass
        except ValueError:
            if bpm_control_var: bpm_control_var.set(bpm_actual)
        except Exception as e_bpm_get_mel_play:
            print(f"Error obteniendo BPM del spinbox para reprod. melodía: {e_bpm_get_mel_play}")


    if not historial_progresiones:
        messagebox.showinfo("Reproducir Melodía", "Primero genera una progresión y una melodía.")
        return

    _raiz, _modo, _estilo, _acordes_hist, ritmo_hist_mel, melodia_para_reproducir = historial_progresiones[-1]

    if not melodia_para_reproducir:
        messagebox.showinfo("Reproducir Melodía", "No se ha generado una melodía para esta progresión.")
        if label_ruta_guardado_var: label_ruta_guardado_var.set("📁 No hay melodía para reproducir.")
        return

    melodia_stream = stream.Part()
    melodia_stream.insert(0, MetronomeMark(number=bpm_actual))
    melodia_stream.insert(0, instrumento_seleccionado_melodia if isinstance(instrumento_seleccionado_melodia, instrument.Instrument) else instrument.Piano())

    current_offset_mel = 0.0
    for nombre_nota, dur_nota_str in melodia_para_reproducir:
        dur_float = float(dur_nota_str)
        elemento_musical = None
        if nombre_nota == "0":
            elemento_musical = note.Rest(quarterLength=dur_float)
        else:
            elemento_musical = note.Note(nombre_nota, quarterLength=dur_float)

        if elemento_musical:
            melodia_stream.insert(current_offset_mel, elemento_musical)
            current_offset_mel += dur_float

    path_temporal_melodia = _export_midi_base(melodia_stream, "melodia_playback", for_playback=True)

    if not path_temporal_melodia or not os.path.exists(path_temporal_melodia):
        if label_ruta_guardado_var: label_ruta_guardado_var.set("📁 Falló preparación para reprod. melodía")
        return

    try:
        if not pygame.mixer.get_init(): pygame.mixer.init()
        pygame.mixer.music.stop()
        if current_piano_roll_instance: current_piano_roll_instance.detener_cursor_reproduccion()

        pygame.mixer.music.load(path_temporal_melodia)
        pygame.mixer.music.play(loops=-1)

        if current_piano_roll_instance and ritmo_hist_mel:
            ritmo_valido_cursor_mel = [float(d) for d in ritmo_hist_mel]
            duracion_total_ms_cursor_mel = calcular_duracion_total_ms(ritmo_valido_cursor_mel, bpm_actual)
            if duracion_total_ms_cursor_mel > 0:
                current_piano_roll_instance.iniciar_cursor_reproduccion(duracion_total_ms_cursor_mel)

        if label_ruta_guardado_var: label_ruta_guardado_var.set(f"🎶 Reprod. Melodía (Bucle) (BPM: {bpm_actual})")
    except Exception as e_play_mel:
        print(f"Error reproducción melodía: {e_play_mel}")
        if label_ruta_guardado_var: label_ruta_guardado_var.set(f"📁 Error reproducción melodía: {e_play_mel}")

def accion_reproducir_todo():
    global historial_progresiones, bpm_actual, label_ruta_guardado_var, bpm_control_var, label_bpm_var
    global instrumento_seleccionado_acordes, instrumento_seleccionado_melodia
    global current_piano_roll_instance

    if bpm_control_var:
        try:
            valor_bpm_spinbox = int(bpm_control_var.get())
            if 20 <= valor_bpm_spinbox <= 300:
                bpm_actual = valor_bpm_spinbox
                if label_bpm_var:
                    label_bpm_var.set(f"BPM: {bpm_actual}")
            else:
                bpm_control_var.set(bpm_actual)
        except tk.TclError:
            pass
        except ValueError:
            if bpm_control_var: bpm_control_var.set(bpm_actual)
        except Exception as e_bpm_get_todo:
            print(f"Error obteniendo BPM del spinbox en Reproducir Todo: {e_bpm_get_todo}")

    if not historial_progresiones:
        if label_ruta_guardado_var:
            label_ruta_guardado_var.set("📁 No hay progresión para reproducir.")
        messagebox.showinfo("Reproducir Todo", "Primero genera una progresión de acordes.")
        return

    _raiz_hist, _modo_hist, _estilo_hist, acordes_actuales_hist, ritmo_de_acordes_actual_hist, melodia_para_reproducir = historial_progresiones[-1]

    if not acordes_actuales_hist and not melodia_para_reproducir:
        if label_ruta_guardado_var:
            label_ruta_guardado_var.set("📁 Nada para reproducir.")
        return

    detener_reproduccion_actual()

    score = stream.Score(id='score_principal')
    score.insert(0, MetronomeMark(number=bpm_actual))

    if acordes_actuales_hist:
        part_acordes = stream.Part(id='acordes')
        if isinstance(instrumento_seleccionado_acordes, instrument.Instrument):
            part_acordes.insert(0, instrumento_seleccionado_acordes)
        else:
            part_acordes.insert(0, instrument.Piano())

        current_offset_acordes = 0.0
        ritmo_acordes_float = [float(r) for r in ritmo_de_acordes_actual_hist] if ritmo_de_acordes_actual_hist else [1.0] * len(acordes_actuales_hist) if acordes_actuales_hist else [1.0]

        for i, ac_data in enumerate(acordes_actuales_hist):
            duracion = ritmo_acordes_float[i % len(ritmo_acordes_float)] if ritmo_acordes_float else 1.0
            elemento_ac = None
            if isinstance(ac_data, str) and ac_data in ("0", "N/A"):
                elemento_ac = note.Rest(quarterLength=duracion)
            elif isinstance(ac_data, list) and ac_data:
                notas_procesadas_ac = []
                for n_str in ac_data:
                    if isinstance(n_str, str):
                        if not re.search(r'\d$', n_str.strip()):
                            notas_procesadas_ac.append(f"{n_str.strip()}4")
                        else:
                            notas_procesadas_ac.append(n_str.strip())
                if notas_procesadas_ac:
                     elemento_ac = chord.Chord(notas_procesadas_ac, quarterLength=duracion)
                else:
                    elemento_ac = note.Rest(quarterLength=duracion)

            if elemento_ac:
                part_acordes.insert(current_offset_acordes, elemento_ac)
            current_offset_acordes += duracion
        if part_acordes.hasMeasures() or part_acordes.flat.notesAndRests:
             score.insert(0, part_acordes)

    if melodia_para_reproducir:
        part_melodia = stream.Part(id='melodia')
        if isinstance(instrumento_seleccionado_melodia, instrument.Instrument):
            part_melodia.insert(0, instrumento_seleccionado_melodia)
        else:
            part_melodia.insert(0, instrument.Piano())

        current_offset_melodia = 0.0
        for nombre_nota_mel, dur_nota_mel_str in melodia_para_reproducir:
            try:
                dur_float_mel = float(dur_nota_mel_str)
                if dur_float_mel <= 0: continue
                elemento_mel = None
                if nombre_nota_mel == "0" or not nombre_nota_mel:
                    elemento_mel = note.Rest(quarterLength=dur_float_mel)
                else:
                    elemento_mel = note.Note(nombre_nota_mel, quarterLength=dur_float_mel)
            except ValueError:
                print(f"Advertencia: Duración de melodía inválida '{dur_nota_mel_str}'. Saltando evento.")
                continue
            except Exception as e_nota_mel:
                print(f"Advertencia: Nota de melodía inválida '{nombre_nota_mel}': {e_nota_mel}. Saltando evento.")
                continue

            if elemento_mel:
                part_melodia.insert(current_offset_melodia, elemento_mel)
            current_offset_melodia += dur_float_mel
        if part_melodia.hasMeasures() or part_melodia.flat.notesAndRests:
            score.insert(0, part_melodia)

    if not score.elements or not score.flat.notesAndRests:
        if label_ruta_guardado_var:
            label_ruta_guardado_var.set("📁 Score vacío, nada para reproducir.")
        return

    path_temporal_todo = _export_midi_base(score, "todo_playback", for_playback=True)

    if not path_temporal_todo or not os.path.exists(path_temporal_todo):
        if label_ruta_guardado_var:
            label_ruta_guardado_var.set("📁 Falló preparación para reprod. todo")
        return

    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.stop()

        pygame.mixer.music.load(path_temporal_todo)
        pygame.mixer.music.play(loops=-1)

        if current_piano_roll_instance and ritmo_de_acordes_actual_hist:
            try:
                ritmo_valido_cursor = [float(d) for d in ritmo_de_acordes_actual_hist if str(d).replace('.', '', 1).isdigit()]
                if ritmo_valido_cursor:
                    duracion_total_ms_cursor = calcular_duracion_total_ms(ritmo_valido_cursor, bpm_actual)
                    if duracion_total_ms_cursor > 0:
                        current_piano_roll_instance.iniciar_cursor_reproduccion(duracion_total_ms_cursor)
            except Exception as e_cursor:
                print(f"Error al calcular o iniciar cursor de reproducción: {e_cursor}")

        if label_ruta_guardado_var:
            label_ruta_guardado_var.set(f"⏯️ Reprod. Todo (Bucle) (BPM: {bpm_actual})")

    except pygame.error as e_pygame_play:
        print(f"Error de Pygame al reproducir 'todo': {e_pygame_play}")
        if label_ruta_guardado_var:
            label_ruta_guardado_var.set(f"📁 Error Pygame: {e_pygame_play}")
        messagebox.showerror("Error de Reproducción", f"Pygame no pudo reproducir el archivo MIDI: {e_pygame_play}")
    except Exception as e_play_todo:
        print(f"Error general en reproducción todo: {e_play_todo}")
        import traceback
        traceback.print_exc()
        if label_ruta_guardado_var:
            label_ruta_guardado_var.set(f"📁 Error reprod. todo: {e_play_todo}")

def accion_espacio_presionado(event=None):
    global label_ruta_guardado_var, ventana_principal, entrada_prompt_texto, spin_bpm

    widget_con_foco = ventana_principal.focus_get()
    if widget_con_foco == entrada_prompt_texto or widget_con_foco == spin_bpm:
        return

    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            if not pygame.mixer.get_init():
                if label_ruta_guardado_var:
                    label_ruta_guardado_var.set("Error de audio al usar barra espaciadora.")
                return

        if pygame.mixer.music.get_busy():
            detener_reproduccion_actual()
        else:
            accion_reproducir_todo()
    except pygame.error as e_pygame:
        print(f"Error de Pygame en accion_espacio_presionado: {e_pygame}")
        if label_ruta_guardado_var:
            label_ruta_guardado_var.set(f"Error de audio: {e_pygame}")
    except Exception as e_espacio:
        print(f"Error inesperado en accion_espacio_presionado: {e_espacio}")
        if label_ruta_guardado_var:
            label_ruta_guardado_var.set("Error inesperado con barra espaciadora.")

def exportar_todos_a_midi():
    global label_ruta_guardado_var, historial_progresiones

    if not historial_progresiones:
        messagebox.showinfo("Exportar", "No hay progresión de acordes para exportar.")
        return

    path_acordes_exportado = exportar_acordes_a_midi_individual(for_playback=False)
    if not path_acordes_exportado:
        messagebox.showerror("Error Exportación", "Falló la exportación de los acordes.")

    _raiz_prog_exp, _modo_prog_exp, _estilo, _acordes_prog_exp, _ritmo_prog_exp, melodia_a_exportar = historial_progresiones[-1]
    path_melodia_exportada = None
    if melodia_a_exportar:
        path_melodia_exportada = exportar_melodia_a_midi_individual(melodia_a_exportar, for_playback=False)

    msg_final_label = []
    if path_acordes_exportado:
        msg_final_label.append(f"🎼 {os.path.basename(path_acordes_exportado)}")
    if path_melodia_exportada:
        msg_final_label.append(f"🎶 {os.path.basename(path_melodia_exportada)}")

    if msg_final_label:
        label_ruta_guardado_var.set(" y ".join(msg_final_label) + " Exportados")
        messagebox.showinfo("Exportación Completa", f"Archivos exportados a:\n{CARPETA_MIDI_EXPORTADO}")
    elif path_acordes_exportado :
        label_ruta_guardado_var.set(f"🎼 {os.path.basename(path_acordes_exportado)} Exportado (Melodía no procesada/generada)")
        messagebox.showwarning("Exportación Parcial", f"Solo los acordes fueron exportados a:\n{CARPETA_MIDI_EXPORTADO}")
    else:
        if not path_acordes_exportado and not melodia_a_exportar:
             messagebox.showinfo("Exportar", "Nada para exportar (no hay acordes ni melodía).")

    abrir_carpeta_midi_exportado()

def accion_enter_en_prompt(event=None):
    global entrada_prompt_texto, label_ruta_guardado_var, ventana_principal

    if entrada_prompt_texto:
        prompt_text = entrada_prompt_texto.get()
        if prompt_text and prompt_text.strip():
            accion_generar_desde_prompt()
        else:
            if label_ruta_guardado_var:
                label_ruta_guardado_var.set("Escribe un prompt antes de presionar Enter.")
            if ventana_principal: # Quitar foco incluso si el prompt está vacío
                ventana_principal.focus_set()
    else:
        print("ADVERTENCIA (Enter en Prompt): El widget entrada_prompt_texto no está inicializado.")


def quitar_foco_de_entradas_al_clic_fondo(event=None):
    global ventana_principal, entrada_prompt_texto, spin_bpm

    if not ventana_principal or not event: return

    widget_clicado = event.widget
    widget_con_foco = ventana_principal.focus_get()

    campos_de_entrada_a_desenfocar = []
    if entrada_prompt_texto: campos_de_entrada_a_desenfocar.append(entrada_prompt_texto)
    if spin_bpm: campos_de_entrada_a_desenfocar.append(spin_bpm)

    widgets_interactivos_que_retienen_foco = (
        tk.Entry, ttk.Entry,
        tk.Spinbox, ttk.Spinbox,
        tk.Text,
        tk.Button, ttk.Button,
        ttk.Combobox,
        tk.Scale, ttk.Scale,
        tk.Scrollbar, ttk.Scrollbar,
        tk.Listbox,
        tk.Menu,
        PianoRoll
    )

    if widget_con_foco in campos_de_entrada_a_desenfocar:
        if widget_clicado != widget_con_foco and \
           not isinstance(widget_clicado, widgets_interactivos_que_retienen_foco):
            ventana_principal.focus_set()
    elif isinstance(widget_con_foco, (tk.Entry, tk.Spinbox)):
        if not isinstance(widget_clicado, widgets_interactivos_que_retienen_foco):
            ventana_principal.focus_set()

def abrir_carpeta_midi_exportado(event=None):
    global label_ruta_guardado_var
    os.makedirs(CARPETA_MIDI_EXPORTADO, exist_ok=True)
    try:
        if os.name == 'nt':
            os.startfile(CARPETA_MIDI_EXPORTADO)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', CARPETA_MIDI_EXPORTADO])
        else:
            subprocess.Popen(['xdg-open', CARPETA_MIDI_EXPORTADO])
    except Exception as e_open:
        print(f"Error al abrir carpeta: {e_open}")
        if label_ruta_guardado_var: label_ruta_guardado_var.set(f"📁 Error al abrir carpeta: {e_open}")

# --- Diálogo de Bienvenida / Lista de Géneros ---
def mostrar_dialogo_bienvenida(parent_window, titulo="¡Bienvenido/a!", mensaje_personalizado=None, mostrar_saludo_inicial=True, color_mensaje=COLOR_DIALOGO_FG):
    dialogo = tk.Toplevel(parent_window)
    dialogo.title(titulo)
    dialogo.configure(bg=COLOR_DIALOGO_BG)
    dialogo.geometry("450x350")
    dialogo.resizable(False, False)

    parent_x = parent_window.winfo_x()
    parent_y = parent_window.winfo_y()
    parent_width = parent_window.winfo_width()
    parent_height = parent_window.winfo_height()
    dialog_width = 450
    dialog_height = 350
    x = parent_x + (parent_width // 2) - (dialog_width // 2)
    y = parent_y + (parent_height // 2) - (dialog_height // 2)
    dialogo.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

    frame_contenido = tk.Frame(dialogo, bg=COLOR_DIALOGO_BG, padx=20, pady=20)
    frame_contenido.pack(expand=True, fill="both")

    if mostrar_saludo_inicial:
        label_saludo = tk.Label(frame_contenido,
                                text="Hola, ¡qué gusto tenerte por aquí!",
                                font=("Segoe UI", 14, "bold"),
                                bg=COLOR_DIALOGO_BG, fg=COLOR_DIALOGO_FG,
                                pady=10)
        label_saludo.pack()

    if mensaje_personalizado:
        label_mensaje = tk.Label(frame_contenido,
                                 text=mensaje_personalizado,
                                 font=("Segoe UI", 10, "bold" if color_mensaje == COLOR_DIALOGO_ERROR_FG else "normal"),
                                 bg=COLOR_DIALOGO_BG, fg=color_mensaje,
                                 pady=8, anchor="w", justify="left", wraplength=400)
        label_mensaje.pack(fill="x")


    label_intro_generos = tk.Label(frame_contenido,
                                   text="Estos son los géneros musicales que te puedo generar por ahora:" if mostrar_saludo_inicial else "Géneros disponibles:",
                                   font=("Segoe UI", 10),
                                   bg=COLOR_DIALOGO_BG, fg=COLOR_DIALOGO_FG,
                                   pady=5, anchor="w", justify="left")
    label_intro_generos.pack(fill="x")

    generos_disponibles = sorted([g.capitalize() for g in INFO_GENERO.keys() if g != "patrones_ritmicos" and isinstance(INFO_GENERO.get(g), dict) and any(INFO_GENERO[g].get(k) for k in INFO_GENERO[g] if k != "patrones_ritmicos")])


    if generos_disponibles:
        frame_lista_generos = tk.Frame(frame_contenido, bg=COLOR_DIALOGO_LISTA_BG, bd=1, relief="solid")
        frame_lista_generos.pack(fill="both", expand=True, pady=10)

        canvas_lista = tk.Canvas(frame_lista_generos, bg=COLOR_DIALOGO_LISTA_BG, highlightthickness=0)
        scrollbar_lista = ttk.Scrollbar(frame_lista_generos, orient="vertical", command=canvas_lista.yview)
        frame_scrollable_lista = tk.Frame(canvas_lista, bg=COLOR_DIALOGO_LISTA_BG)

        frame_scrollable_lista.bind(
            "<Configure>",
            lambda e: canvas_lista.configure(
                scrollregion=canvas_lista.bbox("all")
            )
        )

        canvas_lista.create_window((0, 0), window=frame_scrollable_lista, anchor="nw")
        canvas_lista.configure(yscrollcommand=scrollbar_lista.set)

        for i, genero_item in enumerate(generos_disponibles):
            tk.Label(frame_scrollable_lista, text=f"• {genero_item}",
                     font=("Segoe UI", 10, "italic"), bg=COLOR_DIALOGO_LISTA_BG,
                     fg=COLOR_DIALOGO_FG, anchor="w", padx=10).pack(fill="x", pady=2)

        canvas_lista.pack(side="left", fill="both", expand=True)
        scrollbar_lista.pack(side="right", fill="y")
    else:
        tk.Label(frame_contenido, text="Actualmente no hay géneros cargados.\nPuedes entrenar algunos usando el autoentrenador.",
                 font=("Segoe UI", 10, "italic"), bg=COLOR_DIALOGO_BG, fg="#FFCC00").pack(pady=10)


    boton_ok = ttk.Button(frame_contenido, text="¡Entendido!", command=dialogo.destroy, style="Accent.TButton")
    boton_ok.pack(pady=(15, 0))

    dialogo.transient(parent_window)
    dialogo.grab_set()
    parent_window.wait_window(dialogo)


# --- Configuración de la Interfaz Gráfica ---
def configurar_ventana_principal():
    global frame_info_alternos, frame_info_ruta, frame_ritmo_display, show_alternos
    global ventana_principal, entrada_prompt_texto, combo_cantidad, frame_piano_roll_display
    global ritmo_seleccionado_label_var, label_acordes_generados_var, label_ruta_guardado_var
    global background_label, photo_image, current_piano_roll_instance
    global botones_instrumento_acordes, boton_instr_acordes_seleccionado
    global botones_instrumento_melodia, boton_instr_melodia_seleccionado
    global label_transposicion_var
    global label_bpm_var, bpm_control_var, bpm_frame
    global feedback_status_label, feedback_status_label_var
    global spin_bpm
    global img_corazon, img_pulgar_abajo


    ventana_principal = TkinterDnD.Tk()

    # --- ESTABLECER ICONO DE LA VENTANA ---
    try:
        icon_path = resource_path(os.path.join("sources", "piano.ico")) # Asegúrate que sea la ruta correcta
        if os.path.exists(icon_path):
            if sys.platform.startswith('win'):
                ventana_principal.iconbitmap(icon_path)
            else:
                # Para Linux/macOS, iconphoto es más flexible
                try:
                    # Intenta cargar el PNG original para iconphoto si el ICO da problemas con PhotoImage
                    img_png_path = resource_path(os.path.join("sources", "piano.png"))
                    if os.path.exists(img_png_path):
                        img = Image.open(img_png_path)
                        photo_img = ImageTk.PhotoImage(img)
                        ventana_principal.iconphoto(False, photo_img)
                    elif os.path.exists(icon_path): # Fallback al ICO si el PNG no está pero el ICO sí
                         ventana_principal.iconbitmap(icon_path)
                except Exception as e_img_load:
                    print(f"Advertencia: No se pudo cargar la imagen del icono para la ventana: {e_img_load}")
                    if os.path.exists(icon_path): # Fallback final a iconbitmap si existe el .ico
                            ventana_principal.iconbitmap(icon_path)
        else:
            print(f"Advertencia: Archivo de icono no encontrado en: {icon_path}")
    except Exception as e:
        print(f"Error estableciendo el icono de la ventana: {e}")
    # --- FIN DE ESTABLECER ICONO DE LA VENTANA ---
    
    ruta_corazon_img = os.path.join(RUTA_BASE_PROYECTO, "sources", "corazon.png")
    ruta_pulgar_abajo_img = os.path.join(RUTA_BASE_PROYECTO, "sources", "pulgar_abajo.png")

    try:
        img_corazon = ImageTk.PhotoImage(Image.open(ruta_corazon_img).resize((12, 12)))
        img_pulgar_abajo = ImageTk.PhotoImage(Image.open(ruta_pulgar_abajo_img).resize((12, 12)))
    except Exception as e_img:
        print(f"Error cargando imágenes de feedback: {e_img}")
        img_corazon = None
        img_pulgar_abajo = None


    ventana_principal.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo, add="+")

    show_alternos = tk.BooleanVar(master=ventana_principal, value=False)

    def toggle_textos_alternos_closure(container_widget):
        def toggle():
            if show_alternos.get():
                container_widget.pack(fill="x", pady=(0,3))
            else:
                container_widget.pack_forget()
        return toggle

    menubar = tk.Menu(ventana_principal)
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Exportar MIDI", command=exportar_todos_a_midi)
    menubar.add_cascade(label="Archivo", menu=file_menu)
    edit_menu = tk.Menu(menubar, tearoff=0)
    edit_menu.add_command(label="↺ Deshacer  ctrl + z", command=accion_deshacer)
    edit_menu.add_command(label="↻ Rehacer  ctrl + y", command=accion_rehacer)
    menubar.add_cascade(label="Editar", menu=edit_menu)
    view_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Ver", menu=view_menu)
    ventana_principal.config(menu=menubar)

    ventana_principal.bind('<Control-z>', accion_deshacer)
    ventana_principal.bind('<Control-y>', accion_rehacer)
    ventana_principal.bind('<space>', accion_espacio_presionado)


    ventana_principal.title("NeuraChord")
    ventana_principal.geometry("950x700")
    ventana_principal.configure(bg=COLOR_BG_VENTANA)

    FUENTE_BASE = ("Segoe UI", 10); FUENTE_BOTON = ("Segoe UI", 9)
    FUENTE_ETIQUETA_PROMPT = ("Segoe UI", 11, "bold"); FUENTE_INFO_SECUNDARIA = ("Segoe UI", 8, "italic")
    FUENTE_TRANSPOSICION = ("Segoe UI", 10, "bold")

    estilo_base_boton = {"font": FUENTE_BOTON, "relief": tk.FLAT, "bd": 0, "pady": 5, "padx": 10, "activeforeground": COLOR_BOTON_ACCENTO_FG}
    estilos = {
        "crear_acordes": {**estilo_base_boton, "text": "🎼 Crear Acordes", "bg": COLOR_BOTON_ACCENTO_BG, "fg": COLOR_BOTON_ACCENTO_FG, "activebackground": COLOR_BOTON_ACCENTO_ACTIVE_BG, "width": 15},
        "generar_melodia_lado": {**estilo_base_boton, "text": "🎶 Generar Melodía", "bg": COLOR_BOTON_SECUNDARIO_BG, "fg": COLOR_BOTON_SECUNDARIO_FG, "activebackground": COLOR_BOTON_SECUNDARIO_ACTIVE_BG, "width": 15},
        "nuevo_ritmo": {**estilo_base_boton, "text": "🔁 Nuevo Ritmo", "bg": COLOR_BOTON_SECUNDARIO_BG, "fg": COLOR_BOTON_SECUNDARIO_FG, "activebackground": COLOR_BOTON_SECUNDARIO_ACTIVE_BG, "width": 15},
        "controles_edicion": {**estilo_base_boton, "bg": COLOR_BOTON_CONTROL_BG, "fg": COLOR_BOTON_CONTROL_FG, "activebackground": COLOR_BOTON_CONTROL_ACTIVE_BG, "width": 12},
        "exportar": {**estilo_base_boton, "text": "💾 Exportar MIDI", "bg": COLOR_BOTON_ACCENTO_BG, "fg": COLOR_BOTON_ACCENTO_FG, "activebackground": COLOR_BOTON_ACCENTO_ACTIVE_BG, "width": 15},
        "reproduccion": {**estilo_base_boton, "fg": COLOR_BOTON_SECUNDARIO_FG, "activebackground": COLOR_BOTON_SECUNDARIO_ACTIVE_BG, "width": 18},
        "pausa": {**estilo_base_boton, "text": "⏸ Pausa", "bg": COLOR_BOTON_PAUSA_BG, "fg": COLOR_BOTON_PAUSA_FG, "activebackground": COLOR_BOTON_PAUSA_ACTIVE_BG, "width": 18},
        "instrumentos": {**estilo_base_boton, "bg": COLOR_BOTON_INSTRUMENTO_BG, "fg": COLOR_BOTON_INSTRUMENTO_FG, "activebackground": COLOR_BOTON_INSTRUMENTO_ACTIVE_BG, "width": 8, "pady": 3},
        "feedback_positivo": {
            **estilo_base_boton,
            "text": "👍" if not img_corazon else "", "image": img_corazon if img_corazon else None, "compound": tk.LEFT if img_corazon else tk.NONE,
            "bg": COLOR_FEEDBACK_POSITIVO_BG, "fg": COLOR_FEEDBACK_POSITIVO_FG, "activebackground": COLOR_FEEDBACK_POSITIVO_ACTIVE_BG,
            "width": 55 if img_corazon else 12, "height": 25 if img_corazon else None
        },
        "feedback_negativo": {
            **estilo_base_boton,
            "text": "👎" if not img_pulgar_abajo else "", "image": img_pulgar_abajo if img_pulgar_abajo else None, "compound": tk.LEFT if img_pulgar_abajo else tk.NONE,
            "bg": COLOR_FEEDBACK_NEGATIVO_BG, "fg": COLOR_FEEDBACK_NEGATIVO_FG, "activebackground": COLOR_FEEDBACK_NEGATIVO_ACTIVE_BG,
            "width": 55 if img_pulgar_abajo else 12, "height": 25 if img_pulgar_abajo else None
        }
    }
    estilos["reprod_acordes"] = {**estilos["reproduccion"], "text": "🎹 Reproducir Acordes", "bg": "#6666CC", "activebackground": "#5555AA" }
    estilos["reprod_melodia"] = {**estilos["reproduccion"], "text": "🎶 Reproducir Melodía", "bg": "#6666CC", "activebackground": "#5555AA" }
    estilos["reprod_todo"] = {**estilos["reproduccion"], "text": "⏯️ Reproducir Todo", "bg": "#6666FF", "fg": "#FFFFFF", "activebackground": "#4cae4c"}

    style_ttk = ttk.Style()
    style_ttk.configure("Accent.TButton", background=COLOR_BOTON_ACCENTO_BG, foreground=COLOR_BOTON_ACCENTO_FG, font=FUENTE_BOTON, padding=6)
    style_ttk.map("Accent.TButton", background=[('active', COLOR_BOTON_ACCENTO_ACTIVE_BG)])


    frame_prompt = tk.Frame(ventana_principal, padx=10, pady=5, bg=COLOR_BG_FRAMES)
    frame_prompt.pack(fill="x", pady=(10, 5))
    frame_prompt.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    label_prompt_widget_ref = tk.Label(frame_prompt, text="📝 Prompt:", font=FUENTE_ETIQUETA_PROMPT, bg=COLOR_BG_FRAMES, fg=COLOR_FG_TEXT_PRINCIPAL)
    label_prompt_widget_ref.pack(side="left", padx=(0, 5))
    label_prompt_widget_ref.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    entrada_prompt_texto = tk.Entry(frame_prompt, font=FUENTE_BASE, bg=COLOR_INPUT_BG, fg=COLOR_INPUT_FG, insertbackground=COLOR_INPUT_INSERT, bd=1, relief=tk.SOLID, selectbackground="#005C99", selectforeground=COLOR_INPUT_FG)
    entrada_prompt_texto.pack(side="left", padx=5, expand=True, fill="x")
    entrada_prompt_texto.insert(0, "Reggaeton en Eb major")
    entrada_prompt_texto.bind('<Return>', accion_enter_en_prompt)

    tk.Button(frame_prompt, command=lambda: accion_generar_desde_prompt(usar_markov_override=False), **estilos["crear_acordes"]).pack(side="left", padx=(5, 2))
    tk.Button(frame_prompt, command=accion_generar_melodia, **estilos["generar_melodia_lado"]).pack(side="left", padx=(2, 5))

    boton_like = tk.Button(frame_prompt, command=lambda: accion_feedback(True), **estilos["feedback_positivo"])
    boton_like.pack(side="left", padx=(5, 2), pady=2)
    boton_dislike = tk.Button(frame_prompt, command=lambda: accion_feedback(False), **estilos["feedback_negativo"])
    boton_dislike.pack(side="left", padx=2, pady=2)

    feedback_status_label_var = StringVar(master=ventana_principal, value="")
    feedback_status_label = tk.Label(frame_prompt, textvariable=feedback_status_label_var, font=FUENTE_INFO_SECUNDARIA, bg=COLOR_BG_FRAMES, fg=COLOR_FG_TEXT_PRINCIPAL)
    feedback_status_label.pack(side="left", padx=(10, 0), pady=2)
    feedback_status_label.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    frame_config_acordes = tk.Frame(ventana_principal, padx=10, pady=3, bg=COLOR_BG_FRAMES)
    frame_config_acordes.pack(fill="x", pady=3, padx=10)
    frame_config_acordes.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    espaciado_controles = 70

    label_num_acordes = tk.Label(frame_config_acordes, text="Nº Acordes:", font=FUENTE_BASE, bg=COLOR_BG_FRAMES, fg=COLOR_FG_TEXT_PRINCIPAL)
    label_num_acordes.pack(side="left", padx=(0, 5))
    label_num_acordes.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    s_combo = ttk.Style(); s_combo.theme_use('clam')
    s_combo.configure("TCombobox", fieldbackground=COLOR_INPUT_BG, background=COLOR_BOTON_SECUNDARIO_BG, foreground=COLOR_INPUT_FG, arrowcolor=COLOR_FG_TEXT_PRINCIPAL, bordercolor=COLOR_BG_FRAMES, lightcolor=COLOR_BG_FRAMES, darkcolor=COLOR_BG_FRAMES, relief=tk.FLAT, padding=4)
    s_combo.map('TCombobox', fieldbackground=[('readonly', COLOR_INPUT_BG), ('focus', COLOR_INPUT_BG)], foreground=[('readonly', COLOR_INPUT_FG)], selectbackground=[('readonly', COLOR_INPUT_BG)], selectforeground=[('readonly', COLOR_INPUT_FG)], bordercolor=[('focus', COLOR_BOTON_ACCENTO_BG)])
    combo_cantidad = ttk.Combobox(frame_config_acordes, values=["4", "8", "Sin límite"], state="readonly", font=FUENTE_BASE, width=10, style="TCombobox")
    combo_cantidad.set("Sin límite")
    combo_cantidad.pack(side="left", padx=(0, espaciado_controles))
    combo_cantidad.bind("<<ComboboxSelected>>", actualizar_cantidad_acordes); actualizar_cantidad_acordes()

    tk.Button(frame_config_acordes, **estilos["nuevo_ritmo"], command=accion_nuevo_patron_ritmico).pack(side="left", padx=(0, espaciado_controles))

    bpm_frame = tk.Frame(frame_config_acordes, bg=COLOR_BG_FRAMES)
    bpm_frame.pack(side="left", padx=(0, 0))
    bpm_frame.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    label_bpm_var = StringVar(master=ventana_principal, value=f"BPM: {bpm_actual}")
    label_bpm_widget = tk.Label(bpm_frame, textvariable=label_bpm_var, font=FUENTE_INFO_SECUNDARIA, bg=COLOR_BG_FRAMES, fg=COLOR_FG_TEXT_SECUNDARIO)
    label_bpm_widget.pack(side="left", padx=(0,3))
    label_bpm_widget.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    bpm_control_var = tk.IntVar(master=ventana_principal, value=bpm_actual)
    spin_bpm = tk.Spinbox(
        bpm_frame, from_=20, to=300, textvariable=bpm_control_var, width=4, font=FUENTE_INFO_SECUNDARIA,
        justify="center", bg=COLOR_INPUT_BG, fg=COLOR_INPUT_FG, insertbackground=COLOR_INPUT_INSERT,
        buttonbackground=COLOR_BG_FRAMES, bd=1, relief="sunken", highlightthickness=0,
        command=lambda: label_bpm_var.set(f"BPM: {bpm_control_var.get()}")
    )
    spin_bpm.pack(side="left", padx=(0, espaciado_controles))
    spin_bpm.bind("<FocusOut>", lambda e: label_bpm_var.set(f"BPM: {bpm_control_var.get()}"))

    tk.Button(bpm_frame, text="↾ Subir Semitono", command=accion_subir_semitono, **estilos["controles_edicion"]).pack(side="left", padx=(0, 10))

    label_transposicion_var = StringVar(master=ventana_principal, value="0 st")
    actualizar_display_transposicion()
    label_transposicion_widget = tk.Label(
        bpm_frame, textvariable=label_transposicion_var, font=FUENTE_TRANSPOSICION,
        bg=COLOR_BG_FRAMES, fg=COLOR_TRANSPOSICION_FG, width=6, anchor="center"
    )
    label_transposicion_widget.pack(side="left", padx=(0, 10))
    label_transposicion_widget.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    tk.Button(bpm_frame, text="↿ Bajar Semitono", command=accion_bajar_semitono, **estilos["controles_edicion"]).pack(side="left", padx=(0, 0))

    frame_reproduccion_instrumentos_principal = tk.Frame(ventana_principal, pady=5, bg=COLOR_BG_FRAMES)
    frame_reproduccion_instrumentos_principal.pack(fill="x", padx=10, pady=3)
    frame_reproduccion_instrumentos_principal.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    alternos_container = tk.Frame(frame_reproduccion_instrumentos_principal, bg=COLOR_BG_FRAMES)

    ritmo_seleccionado_label_var = StringVar(master=ventana_principal, value="Ritmo Usado: N/A")
    frame_ritmo_display = tk.Frame(alternos_container, pady=0, padx=0, bg=COLOR_BG_FRAMES)
    frame_ritmo_display.pack(fill="x")
    frame_ritmo_display.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    label_ritmo_widget = tk.Label(frame_ritmo_display, textvariable=ritmo_seleccionado_label_var, font=FUENTE_INFO_SECUNDARIA,
                                  fg=COLOR_FG_TEXT_SECUNDARIO, bg=COLOR_BG_FRAMES, anchor="w")
    label_ritmo_widget.pack(fill="x", padx=10)
    label_ritmo_widget.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    frame_info_salida = tk.Frame(alternos_container, pady=0, padx=0, bg=COLOR_BG_FRAMES)
    frame_info_salida.pack(fill="x")
    frame_info_salida.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    label_acordes_generados_var = StringVar(master=ventana_principal, value="🧾 Acordes: (aún no generados)")
    label_acordes_widget = tk.Label(frame_info_salida, textvariable=label_acordes_generados_var, font=("Consolas", 9),
                                   anchor="w", justify=tk.LEFT, bg=COLOR_BG_FRAMES, fg=COLOR_FG_TEXT_PRINCIPAL)
    label_acordes_widget.pack(fill="x", padx=10)
    label_acordes_widget.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    toggle_textos_alternos_final = toggle_textos_alternos_closure(alternos_container)
    view_menu.add_checkbutton(label="Ver textos alternos",
                              variable=show_alternos,
                              onvalue=True, offvalue=False,
                              command=toggle_textos_alternos_final)
    view_menu.add_command(label="Listado de Géneros", command=lambda: mostrar_dialogo_bienvenida(ventana_principal))
    view_menu.add_separator()

    toggle_textos_alternos_final()

    frame_botones_reproduccion = tk.Frame(frame_reproduccion_instrumentos_principal, bg=COLOR_BG_FRAMES)
    frame_botones_reproduccion.pack(fill="x", pady=(0, 5))
    frame_botones_reproduccion.columnconfigure(0, weight=1); frame_botones_reproduccion.columnconfigure(1, weight=1)
    frame_botones_reproduccion.columnconfigure(2, weight=1); frame_botones_reproduccion.columnconfigure(3, weight=1)

    tk.Button(frame_botones_reproduccion, **estilos["reprod_acordes"], command=reproducir_midi_acordes).grid(row=0, column=0, sticky="ew", padx=(0, 2))
    tk.Button(frame_botones_reproduccion, **estilos["pausa"], command=detener_reproduccion_actual).grid(row=0, column=1, sticky="ew", padx=2)
    tk.Button(frame_botones_reproduccion, **estilos["reprod_todo"], command=accion_reproducir_todo).grid(row=0, column=2, sticky="ew", padx=2)
    tk.Button(frame_botones_reproduccion, **estilos["reprod_melodia"], command=reproducir_midi_melodia).grid(row=0, column=3, sticky="ew", padx=(2, 0))


    frame_paneles_instrumentos = tk.Frame(frame_reproduccion_instrumentos_principal, bg=COLOR_BG_FRAMES)
    frame_paneles_instrumentos.pack(fill="x", pady=(5, 0))
    frame_paneles_instrumentos.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    frame_panel_acordes = tk.Frame(frame_paneles_instrumentos, bg=COLOR_BG_FRAMES)
    frame_panel_acordes.pack(side="left", expand=True, padx=(0,5), fill="x")
    frame_panel_acordes.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    frame_instr_acordes = tk.Frame(frame_panel_acordes, bg=COLOR_BG_FRAMES)
    frame_instr_acordes.pack(pady=(0,0), fill="x", anchor="center")
    frame_instr_acordes.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    label_instr_ac_widget = tk.Label(frame_instr_acordes, text="Instr. Acordes:", font=FUENTE_INFO_SECUNDARIA, bg=COLOR_BG_FRAMES, fg=COLOR_FG_TEXT_SECUNDARIO)
    label_instr_ac_widget.pack(side="left", padx=(0, 3))
    label_instr_ac_widget.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    botones_instrumento_acordes.clear()
    instr_ac_opciones = [("Piano", instrument.KeyboardInstrument), ("Pad", instrument.StringInstrument), ("Synth Pluck", instrument.Marimba)]
    for nombre, clase_instr_ac in instr_ac_opciones:
        btn_ac = tk.Button(frame_instr_acordes, text=nombre, **estilos["instrumentos"])
        btn_ac.config(command=lambda ci=clase_instr_ac, b=btn_ac: seleccionar_instrumento_para_acordes(ci, b))
        btn_ac.pack(side="left", padx=1, expand=True, fill="x")
        botones_instrumento_acordes.append(btn_ac)
    if botones_instrumento_acordes:
        seleccionar_instrumento_para_acordes(instr_ac_opciones[0][1], botones_instrumento_acordes[0])

    frame_panel_melodia = tk.Frame(frame_paneles_instrumentos, bg=COLOR_BG_FRAMES)
    frame_panel_melodia.pack(side="right", expand=True, padx=(5,0), fill="x")
    frame_panel_melodia.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    frame_instr_melodia = tk.Frame(frame_panel_melodia, bg=COLOR_BG_FRAMES)
    frame_instr_melodia.pack(pady=(0,0), fill="x", anchor="center")
    frame_instr_melodia.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    label_instr_mel_widget = tk.Label(frame_instr_melodia, text="Instr. Melodía:", font=FUENTE_INFO_SECUNDARIA, bg=COLOR_BG_FRAMES, fg=COLOR_FG_TEXT_SECUNDARIO)
    label_instr_mel_widget.pack(side="left", padx=(0, 3))
    label_instr_mel_widget.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    botones_instrumento_melodia.clear()
    instr_mel_opciones = [("Piano", instrument.KeyboardInstrument), ("Voz Lead", instrument.Choir), ("Kalimba", instrument.Kalimba)]
    for nombre_mel, clase_instr_mel in instr_mel_opciones:
        btn_mel = tk.Button(frame_instr_melodia, text=nombre_mel, **estilos["instrumentos"])
        btn_mel.config(command=lambda ci=clase_instr_mel, b=btn_mel: seleccionar_instrumento_para_melodia(ci, b))
        btn_mel.pack(side="left", padx=1, expand=True, fill="x")
        botones_instrumento_melodia.append(btn_mel)
    if botones_instrumento_melodia:
         seleccionar_instrumento_para_melodia(instr_mel_opciones[0][1], botones_instrumento_melodia[0])


    frame_contenedor_piano_roll = tk.Frame(ventana_principal, bg=COLOR_PIANO_ROLL_BG, bd=0)
    frame_contenedor_piano_roll.pack(pady=5, padx=10, fill="both", expand=True)
    frame_contenedor_piano_roll.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    frame_piano_roll_display = tk.Frame(
        frame_contenedor_piano_roll,
        relief=tk.FLAT,
        borderwidth=0,
        bg=COLOR_PIANO_ROLL_BG
    )
    frame_piano_roll_display.pack(fill="both", expand=True, padx=0, pady=0)

    try:
        current_piano_roll_instance = PianoRoll(frame_piano_roll_display, [], [])
        current_piano_roll_instance.pack(fill="both", expand=True)
    except Exception as e_pr_init:
        print(f"Error inicializando PianoRoll: {e_pr_init}")
        placeholder_label_piano_roll = tk.Label(frame_piano_roll_display, text="⚠️ Error al cargar Piano Roll ⚠️",
                                                bg=COLOR_PIANO_ROLL_BG, font=("Segoe UI", 14, "bold"), fg="#FF0000")
        placeholder_label_piano_roll.pack(padx=20, pady=20, expand=True, fill="both")
        placeholder_label_piano_roll.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    try:
        if not pygame.mixer.get_init(): pygame.mixer.init()
    except pygame.error as e_pygame:
        print(f"⚠️ Advertencia: No se pudo inicializar Pygame Mixer: {e_pygame}. La reproducción no funcionará.")
        messagebox.showwarning("Error de Audio",
                               "No se pudo inicializar el sistema de audio (Pygame Mixer).\n"
                               "La reproducción de MIDI no estará disponible.\n"
                               "Asegúrate de tener SDL_mixer instalado si estás en Linux, o revisa tu configuración de audio.")

    frame_info_ruta = tk.Frame(ventana_principal, pady=3, padx=10, bg=COLOR_BG_FRAMES)
    frame_info_ruta.pack(fill="x", side="bottom")
    frame_info_ruta.bind("<Button-1>", quitar_foco_de_entradas_al_clic_fondo)

    label_ruta_guardado_var = StringVar(master=ventana_principal, value="📁 (Listo)")
    label_ruta_clickable = tk.Label(frame_info_ruta, textvariable=label_ruta_guardado_var,
                                   font=FUENTE_INFO_SECUNDARIA, fg=COLOR_FG_TEXT_SECUNDARIO,
                                   bg=COLOR_BG_FRAMES, anchor="w", cursor="hand2")
    label_ruta_clickable.pack(fill="x")
    label_ruta_clickable.bind("<Button-1>", abrir_carpeta_midi_exportado)

    ventana_principal.after(100, lambda: mostrar_dialogo_bienvenida(ventana_principal))

    ventana_principal.mainloop()

if __name__ == "__main__":
    os.makedirs(CARPETA_MIDI_EXPORTADO, exist_ok=True)
    os.makedirs(CARPETA_TEMP_PLAYBACK, exist_ok=True)
    configurar_ventana_principal()
