import tkinter as tk
from tkinter import ttk, Canvas
from music21 import pitch, note as m21_note, chord as m21_chord # Importar note y chord
from music21.harmony import ChordSymbol
import pygame
import sys
import customtkinter as ctk # Asumiendo que usas customtkinter

class PianoRoll(ctk.CTkFrame): # o tk.Frame si no usas customtkinter
    def __init__(self, parent, acordes_progresion, ritmo_progresion=None, melodia_data=None, base_pixeles_por_pulso=60):
        # --- Colores Base (se mantienen) ---
        self.COLOR_CANVAS_BG = "#1C1C1C"
        self.COLOR_LINEAS_FINAS = "#404040"
        self.COLOR_TEXTO_TECLAS = "#B0B0B0"
        self.COLOR_NOTA_RELLENO = "#3A7EBF"
        self.COLOR_NOTA_BORDE = "#70A9E9"
        self.COLOR_TECLA_BLANCA_BG = "#2E2E2E"
        self.COLOR_TECLA_NEGRA_BG = "#202020"
        self.COLOR_TECLA_BORDE = self.COLOR_LINEAS_FINAS
        self.COLOR_RULER_BG = "#252525"
        self.COLOR_PLAYHEAD = "#FF5733"
        self.COLOR_KEYBOARD_BG = "#1A1A1A"
        self.COLOR_MELODIA_RELLENO = "#FFA500" # Naranja para la melodía
        self.EDGE_SCROLL_SLIDER_COLOR = "#6E6E6E"
        self.EDGE_SCROLL_SLIDER_ACTIVE_COLOR = "#858585"

        super().__init__(parent, fg_color=self.COLOR_CANVAS_BG)

        self.acordes_progresion = acordes_progresion if acordes_progresion else []
        self.ritmo_progresion = ritmo_progresion if ritmo_progresion else []
        self.melodia_data = melodia_data if melodia_data else []

        self.base_pixeles_por_pulso = base_pixeles_por_pulso
        self.zoom_level = 1.0
        self.min_zoom = 0.2
        self.max_zoom = 5.0
        self.zoom_step = 0.1
        self.pixeles_por_pulso = self.base_pixeles_por_pulso * self.zoom_level

        self.ancho_teclas_fijo = 50
        self.alto_fila_nota = 12
        self.alto_regla_compases = 25
        self.pulsos_por_compas_visual = 4

        self.midi_note_min = 24  # C1
        self.midi_note_max = 132 # C10

        self.scrollregion_height_contenido_notas = (self.midi_note_max - self.midi_note_min + 1) * self.alto_fila_nota
        self.min_compases_visuales_deseados = 32

        initial_width_solo_acordes = self.min_compases_visuales_deseados * self.pulsos_por_compas_visual * self.pixeles_por_pulso + 20
        self.scrollregion_width_solo_acordes = initial_width_solo_acordes

        self.playhead_line_pianoroll = None
        self.playhead_line_ruler = None
        self.is_playing = False
        self.total_duration_ms = 0
        self.playback_update_job = None
        self.current_playback_time_ms = 0

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

        self.esquina_superior_izquierda = tk.Frame(self, width=self.ancho_teclas_fijo, height=self.alto_regla_compases, bg=self.COLOR_RULER_BG)
        self.esquina_superior_izquierda.grid(row=0, column=0, sticky="nsew")
        self.ruler_canvas = Canvas(self, bg=self.COLOR_RULER_BG, height=self.alto_regla_compases, bd=0, highlightthickness=0)
        self.ruler_canvas.grid(row=0, column=1, sticky="nsew")
        self.keyboard_canvas = Canvas(self, width=self.ancho_teclas_fijo, bg=self.COLOR_KEYBOARD_BG, bd=0, highlightthickness=0)
        self.keyboard_canvas.grid(row=1, column=0, sticky="nsew")
        self.pianoroll_canvas = Canvas(self, bg=self.COLOR_CANVAS_BG, bd=0, highlightthickness=0)
        self.pianoroll_canvas.grid(row=1, column=1, sticky="nsew")

        self.hbar = ctk.CTkScrollbar(
            self, orientation="horizontal", command=self._on_hscroll_main_area,
            fg_color=self.COLOR_CANVAS_BG, button_color=self.EDGE_SCROLL_SLIDER_COLOR,
            button_hover_color=self.EDGE_SCROLL_SLIDER_ACTIVE_COLOR, corner_radius=8, width=6, border_spacing=4
        )
        self.vbar = ctk.CTkScrollbar(
            self, orientation="vertical", command=self._on_vscroll_synced,
            fg_color=self.COLOR_CANVAS_BG, button_color=self.EDGE_SCROLL_SLIDER_COLOR,
            button_hover_color=self.EDGE_SCROLL_SLIDER_ACTIVE_COLOR, corner_radius=8, width=15, border_spacing=3
        )

        self.pianoroll_canvas.configure(xscrollcommand=self._on_pianoroll_xscroll, yscrollcommand=self._on_pianoroll_yscroll)
        self.keyboard_canvas.configure(yscrollcommand=self._on_keyboard_yscroll)

        self.vbar.grid(row=1, column=2, sticky="ns", padx=0, pady=0)
        self.hbar.grid(row=2, column=1, sticky="ew", padx=0, pady=0)

        self.pianoroll_canvas.bind("<Configure>", self.on_canvas_configure)
        common_zoom_elements = [self.pianoroll_canvas, self.keyboard_canvas, self.ruler_canvas, self.esquina_superior_izquierda]
        for elem in common_zoom_elements:
            elem.bind("<Control-MouseWheel>", self._on_zoom_scroll)
            if sys.platform == "darwin": elem.bind("<Command-MouseWheel>", self._on_zoom_scroll)
            elif sys.platform.startswith("linux"):
                elem.bind("<Control-Button-4>", self._on_zoom_scroll); elem.bind("<Control-Button-5>", self._on_zoom_scroll)
        scroll_v_elements = [self.pianoroll_canvas, self.keyboard_canvas]
        for elem in scroll_v_elements:
            elem.bind("<MouseWheel>", self._on_vertical_mouse_scroll)
            if sys.platform.startswith("linux"): elem.bind("<Button-4>", self._on_vertical_mouse_scroll); elem.bind("<Button-5>", self._on_vertical_mouse_scroll)
        scroll_h_elements = [self.pianoroll_canvas, self.ruler_canvas]
        for elem in scroll_h_elements:
            elem.bind("<Shift-MouseWheel>", self._on_horizontal_mouse_scroll)
            if sys.platform.startswith("linux"): elem.bind("<Shift-Button-4>", self._on_horizontal_mouse_scroll); elem.bind("<Shift-Button-5>", self._on_horizontal_mouse_scroll)

        self.after(10, self.force_initial_redraw)

    def _create_rounded_rectangle(self, canvas_obj, x1, y1, x2, y2, radius, **kwargs):
        fill_color = kwargs.get('fill', '')
        outline_color = kwargs.get('outline', '')
        border_width = kwargs.get('width', 0)
        effective_outline_color_for_items = "" if border_width == 0 else outline_color
        _x1_abs, _x2_abs = min(x1, x2), max(x1, x2)
        _y1_abs, _y2_abs = min(y1, y2), max(y1, y2)
        x1, x2, y1, y2 = _x1_abs, _x2_abs, _y1_abs, _y2_abs
        min_dim_half = min(x2 - x1, y2 - y1) / 2.0
        if radius > min_dim_half: radius = min_dim_half
        if radius < 0: radius = 0
        if radius == 0:
            canvas_obj.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline=effective_outline_color_for_items, width=border_width)
            return
        if fill_color:
            if (x2 - x1 > 2 * radius) and (y2 - y1 > 2 * radius): canvas_obj.create_rectangle(x1 + radius, y1 + radius, x2 - radius, y2 - radius, fill=fill_color, outline="")
            if (x2 - x1 > 2 * radius): canvas_obj.create_rectangle(x1 + radius, y1, x2 - radius, y1 + radius, fill=fill_color, outline="")
            if (x2 - x1 > 2 * radius): canvas_obj.create_rectangle(x1 + radius, y2 - radius, x2 - radius, y2, fill=fill_color, outline="")
            if (y2 - y1 > 2 * radius): canvas_obj.create_rectangle(x1, y1 + radius, x1 + radius, y2 - radius, fill=fill_color, outline="")
            if (y2 - y1 > 2 * radius): canvas_obj.create_rectangle(x2 - radius, y1 + radius, x2, y2 - radius, fill=fill_color, outline="")
        canvas_obj.create_arc(x1, y1, x1 + 2 * radius, y1 + 2 * radius, start=90, extent=90, style=tk.PIESLICE, fill=fill_color, outline=effective_outline_color_for_items, width=border_width)
        canvas_obj.create_arc(x2 - 2 * radius, y1, x2, y1 + 2 * radius, start=0, extent=90, style=tk.PIESLICE, fill=fill_color, outline=effective_outline_color_for_items, width=border_width)
        canvas_obj.create_arc(x1, y2 - 2 * radius, x1 + 2 * radius, y2, start=180, extent=90, style=tk.PIESLICE, fill=fill_color, outline=effective_outline_color_for_items, width=border_width)
        canvas_obj.create_arc(x2 - 2 * radius, y2 - 2 * radius, x2, y2, start=270, extent=90, style=tk.PIESLICE, fill=fill_color, outline=effective_outline_color_for_items, width=border_width)
        if border_width > 0 and outline_color:
            if (x2 - x1 > 2 * radius): canvas_obj.create_line(x1 + radius, y1, x2 - radius, y1, fill=outline_color, width=border_width)
            if (x2 - x1 > 2 * radius): canvas_obj.create_line(x1 + radius, y2, x2 - radius, y2, fill=outline_color, width=border_width)
            if (y2 - y1 > 2 * radius): canvas_obj.create_line(x1, y1 + radius, x1, y2 - radius, fill=outline_color, width=border_width)
            if (y2 - y1 > 2 * radius): canvas_obj.create_line(x2, y1 + radius, x2, y2 - radius, fill=outline_color, width=border_width)

    def _on_zoom_scroll(self, event):
        current_view_x_tuple = self.pianoroll_canvas.xview()
        current_center_x_fraction = current_view_x_tuple[0]
        delta_zoom = 0
        if sys.platform == "darwin": delta_zoom = event.delta
        elif sys.platform.startswith("linux"):
            if event.num == 4: delta_zoom = 1
            elif event.num == 5: delta_zoom = -1
            else: delta_zoom = event.delta / 120 if hasattr(event, 'delta') else 0
        else: delta_zoom = event.delta / 120
        if delta_zoom > 0: self.zoom_in()
        elif delta_zoom < 0: self.zoom_out()
        self.update_idletasks()
        if self.scrollregion_width_solo_acordes > 0:
            self.pianoroll_canvas.xview_moveto(current_center_x_fraction)
            self.ruler_canvas.xview_moveto(current_center_x_fraction)
            self._on_pianoroll_xscroll(*self.pianoroll_canvas.xview())
        return "break"

    def _on_vertical_mouse_scroll(self, event):
        scroll_amount = 0
        if sys.platform.startswith("linux"):
            if event.num == 4: scroll_amount = -1
            elif event.num == 5: scroll_amount = 1
        elif hasattr(event, 'delta'):
            if event.delta > 0: scroll_amount = -1
            elif event.delta < 0: scroll_amount = 1
        if scroll_amount != 0:
            self.pianoroll_canvas.yview_scroll(scroll_amount, "units")
            self.keyboard_canvas.yview_scroll(scroll_amount, "units")
        return "break"

    def _on_horizontal_mouse_scroll(self, event):
        scroll_amount = 0
        if sys.platform.startswith("linux"):
            if event.num == 4: scroll_amount = -1
            elif event.num == 5: scroll_amount = 1
        elif hasattr(event, 'delta'):
            if event.delta > 0: scroll_amount = -1
            elif event.delta < 0: scroll_amount = 1
        if scroll_amount != 0:
            self.pianoroll_canvas.xview_scroll(scroll_amount, "units")
            self.ruler_canvas.xview_scroll(scroll_amount, "units")
        return "break"

    def set_zoom(self, new_zoom_level):
        self.zoom_level = max(self.min_zoom, min(new_zoom_level, self.max_zoom))
        self.pixeles_por_pulso = self.base_pixeles_por_pulso * self.zoom_level
        self.force_initial_redraw()

    def zoom_in(self, event=None): self.set_zoom(self.zoom_level * (1 + self.zoom_step))
    def zoom_out(self, event=None): self.set_zoom(self.zoom_level / (1 + self.zoom_step))

    def actualizar_datos(self, acordes_progresion, ritmo_progresion, melodia_data=None):
        self.acordes_progresion = acordes_progresion if acordes_progresion else []
        self.ritmo_progresion = ritmo_progresion if ritmo_progresion else []
        self.melodia_data = melodia_data if melodia_data else []
        self.force_initial_redraw() # Esto llamará a redraw_all_elements y luego a centrar_vista_vertical

    def _on_hscroll_main_area(self, *args):
        self.pianoroll_canvas.xview(*args)
        self.ruler_canvas.xview(*args)

    def _on_pianoroll_xscroll(self, first, last):
        self.hbar.set(first, last)
        self.ruler_canvas.xview_moveto(first)

    def _on_vscroll_synced(self, *args):
        self.pianoroll_canvas.yview(*args)
        self.keyboard_canvas.yview(*args)

    def _on_pianoroll_yscroll(self, first, last):
        self.vbar.set(first, last)
        self.keyboard_canvas.yview_moveto(first)

    def _on_keyboard_yscroll(self, first, last):
        self.vbar.set(first, last)
        self.pianoroll_canvas.yview_moveto(first)

    def force_initial_redraw(self):
        self.pixeles_por_pulso = self.base_pixeles_por_pulso * self.zoom_level
        duracion_total_en_pulsos_progresion = 0
        if self.ritmo_progresion:
            try: duracion_total_en_pulsos_progresion = sum(float(d) for d in self.ritmo_progresion)
            except ValueError: duracion_total_en_pulsos_progresion = len(self.acordes_progresion)
        elif self.acordes_progresion: duracion_total_en_pulsos_progresion = len(self.acordes_progresion)
        min_pulsos_visuales = self.min_compases_visuales_deseados * self.pulsos_por_compas_visual
        duracion_total_en_pulsos_para_ancho = max(duracion_total_en_pulsos_progresion, min_pulsos_visuales)
        ancho_contenido_acordes_calculado = duracion_total_en_pulsos_para_ancho * self.pixeles_por_pulso
        self.scrollregion_width_solo_acordes = ancho_contenido_acordes_calculado + 20
        self.scrollregion_height_contenido_notas = (self.midi_note_max - self.midi_note_min + 1) * self.alto_fila_nota
        self.keyboard_canvas.config(scrollregion=(0, 0, self.ancho_teclas_fijo, self.scrollregion_height_contenido_notas))
        self.pianoroll_canvas.config(scrollregion=(0, 0, self.scrollregion_width_solo_acordes, self.scrollregion_height_contenido_notas))
        self.ruler_canvas.config(scrollregion=(0, 0, self.scrollregion_width_solo_acordes, self.alto_regla_compases))
        self.redraw_all_elements()
        self.centrar_vista_vertical() # Llamar después de redibujar todo

    def on_canvas_configure(self, event):
        self.redraw_all_elements()
        # Considerar si se quiere recentrar también al reconfigurar el canvas (ej. cambio de tamaño de ventana)
        # self.centrar_vista_vertical() # Descomentar si se desea este comportamiento

    def calcular_nota_midi_promedio(self):
        """Calcula la nota MIDI promedio de la progresión actual (acordes y melodía)."""
        todas_las_notas_midi = []
        # Notas de los acordes
        for item_acorde in self.acordes_progresion:
            if isinstance(item_acorde, list):
                for nota_str in item_acorde:
                    try:
                        p = pitch.Pitch(nota_str)
                        todas_las_notas_midi.append(p.midi)
                    except: continue
            elif isinstance(item_acorde, str) and item_acorde.startswith("SN_"): # Notas individuales
                try:
                    p = pitch.Pitch(item_acorde[3:])
                    todas_las_notas_midi.append(p.midi)
                except: continue

        # Notas de la melodía
        if self.melodia_data:
            for nombre_nota_mel, _ in self.melodia_data:
                if nombre_nota_mel != "0" and nombre_nota_mel != "N/A":
                    try:
                        p_mel = pitch.Pitch(nombre_nota_mel)
                        todas_las_notas_midi.append(p_mel.midi)
                    except: continue
        
        if todas_las_notas_midi:
            return sum(todas_las_notas_midi) / len(todas_las_notas_midi)
        return 60 # Fallback a C4 (MIDI 60) si no hay notas

    def centrar_vista_vertical(self):
        """Centra la vista vertical del piano roll alrededor de la nota promedio o C4."""
        nota_midi_objetivo = self.calcular_nota_midi_promedio()
        
        # Asegurar que la nota objetivo esté dentro del rango visible
        nota_midi_objetivo = max(self.midi_note_min, min(nota_midi_objetivo, self.midi_note_max))

        # Calcular la posición Y de la nota objetivo en el scrollregion
        # El scrollregion va de 0 (arriba, midi_note_max) a scrollregion_height (abajo, midi_note_min)
        pos_y_nota_objetivo = (self.midi_note_max - nota_midi_objetivo) * self.alto_fila_nota

        # Calcular la fracción para yview_moveto
        # Queremos que pos_y_nota_objetivo esté en el centro de la parte visible del canvas
        altura_visible_canvas = self.pianoroll_canvas.winfo_height()
        fraccion_scroll = (pos_y_nota_objetivo - (altura_visible_canvas / 2)) / self.scrollregion_height_contenido_notas
        
        # Asegurar que la fracción esté entre 0 y 1
        fraccion_scroll = max(0.0, min(fraccion_scroll, 1.0 - (altura_visible_canvas / self.scrollregion_height_contenido_notas if self.scrollregion_height_contenido_notas > 0 else 0) ))

        self.pianoroll_canvas.yview_moveto(fraccion_scroll)
        self.keyboard_canvas.yview_moveto(fraccion_scroll) # Sincronizar teclado
        self._on_pianoroll_yscroll(fraccion_scroll, fraccion_scroll + (altura_visible_canvas / self.scrollregion_height_contenido_notas if self.scrollregion_height_contenido_notas > 0 else 0)) # Actualizar scrollbar
        print(f"INFO (PianoRoll): Vista vertical centrada en MIDI ~{int(nota_midi_objetivo)} (fracción: {fraccion_scroll:.2f})")


    def redraw_all_elements(self):
        self.keyboard_canvas.delete("all")
        self.pianoroll_canvas.delete("all")
        self.ruler_canvas.delete("all")

        self.dibujar_fondo_grisado_y_lineas_compas_verticales()
        self.dibujar_teclas()
        self.dibujar_numeros_de_compas_en_regla()
        self.dibujar_acordes_mejorado(self.acordes_progresion, self.ritmo_progresion)
        self.dibujar_melodia()

        if self.is_playing and self.total_duration_ms > 0:
            current_progress_ms = self.current_playback_time_ms
            progreso_fraccional = (current_progress_ms % self.total_duration_ms) / self.total_duration_ms if self.total_duration_ms > 0 else 0
            progreso_fraccional = min(max(0, progreso_fraccional), 1)
            duracion_total_pulsos_base = sum(float(d) for d in self.ritmo_progresion) if self.ritmo_progresion else 0
            ancho_total_progresion_px = duracion_total_pulsos_base * self.pixeles_por_pulso
            playhead_x_pianoroll = progreso_fraccional * ancho_total_progresion_px
            if self.playhead_line_pianoroll: self.pianoroll_canvas.delete(self.playhead_line_pianoroll)
            if self.playhead_line_ruler: self.ruler_canvas.delete(self.playhead_line_ruler)
            self.playhead_line_pianoroll = self.pianoroll_canvas.create_line(playhead_x_pianoroll, 0, playhead_x_pianoroll, self.scrollregion_height_contenido_notas, fill=self.COLOR_PLAYHEAD, width=2, tags="playhead_pianoroll")
            self.playhead_line_ruler = self.ruler_canvas.create_line(playhead_x_pianoroll, 0, playhead_x_pianoroll, self.alto_regla_compases, fill=self.COLOR_PLAYHEAD, width=2, tags="playhead_ruler")

    def dibujar_melodia(self):
        if not self.melodia_data: return
        current_x_melodia = 0.0
        corner_radius_melodia = 2
        for nombre_nota_con_octava, duracion_nota_pulsos_str in self.melodia_data:
            duracion_nota_pulsos = float(duracion_nota_pulsos_str)
            ancho_visual_nota_melodia = duracion_nota_pulsos * self.pixeles_por_pulso
            if nombre_nota_con_octava == "0" or nombre_nota_con_octava == "N/A":
                current_x_melodia += ancho_visual_nota_melodia
                continue
            if nombre_nota_con_octava in self.mapeo:
                y_coord_superior_nota_melodia = self.mapeo[nombre_nota_con_octava]
                try:
                    p_check_mel = pitch.Pitch(nombre_nota_con_octava)
                    if not (self.midi_note_min <= p_check_mel.midi <= self.midi_note_max):
                        current_x_melodia += ancho_visual_nota_melodia
                        continue
                except:
                    current_x_melodia += ancho_visual_nota_melodia
                    continue
                note_x1 = current_x_melodia
                note_y1 = y_coord_superior_nota_melodia
                note_x2 = current_x_melodia + ancho_visual_nota_melodia
                note_y2 = y_coord_superior_nota_melodia + self.alto_fila_nota
                self._create_rounded_rectangle(self.pianoroll_canvas, note_x1, note_y1, note_x2, note_y2, radius=corner_radius_melodia, fill=self.COLOR_MELODIA_RELLENO, width=0)
            current_x_melodia += ancho_visual_nota_melodia

    def dibujar_fondo_grisado_y_lineas_compas_verticales(self):
        num_filas_totales = self.midi_note_max - self.midi_note_min + 1
        for i in range(num_filas_totales):
            y = i * self.alto_fila_nota
            midi_val_actual = self.midi_note_max - i
            p_fila = pitch.Pitch(midi_val_actual)
            es_tecla_negra_fila = '#' in p_fila.name or '-' in p_fila.name
            color_fondo_fila = self.COLOR_TECLA_NEGRA_BG if es_tecla_negra_fila else self.COLOR_TECLA_BLANCA_BG
            self.pianoroll_canvas.create_rectangle(0, y, self.scrollregion_width_solo_acordes, y + self.alto_fila_nota, fill=color_fondo_fila, outline="", tags="background_fill")
        for i in range(num_filas_totales + 1):
            y_linea = i * self.alto_fila_nota
            self.pianoroll_canvas.create_line(0, y_linea, self.scrollregion_width_solo_acordes, y_linea, fill=self.COLOR_LINEAS_FINAS, width=1, tags="background_lines")
        pixeles_por_compas_visual = self.pulsos_por_compas_visual * self.pixeles_por_pulso
        if pixeles_por_compas_visual <= 0: return
        num_lineas_compas_a_dibujar = self.scrollregion_width_solo_acordes // pixeles_por_compas_visual
        for i in range(int(num_lineas_compas_a_dibujar) + 1):
            x_pos_linea = i * pixeles_por_compas_visual
            self.pianoroll_canvas.create_line(x_pos_linea, 0, x_pos_linea, self.scrollregion_height_contenido_notas, fill=self.COLOR_LINEAS_FINAS, width=1, dash=(2, 4), tags="compas_lines_vertical")

    def dibujar_teclas(self):
        self.mapeo = {}
        self.keyboard_canvas.create_rectangle(0, 0, self.ancho_teclas_fijo, self.scrollregion_height_contenido_notas, fill=self.COLOR_KEYBOARD_BG, outline="")
        for midi_val in range(self.midi_note_max, self.midi_note_min - 1, -1):
            p = pitch.Pitch(midi_val)
            nombre_nota_original_con_octava = p.nameWithOctave
            nombre_nota_display = nombre_nota_original_con_octava.replace('-', 'b')
            es_tecla_negra = '#' in p.name or '-' in p.name
            y_pos_tecla = (self.midi_note_max - midi_val) * self.alto_fila_nota
            color_rect_tecla = self.COLOR_TECLA_NEGRA_BG if es_tecla_negra else self.COLOR_TECLA_BLANCA_BG
            ancho_dibujo_tecla = self.ancho_teclas_fijo - (5 if es_tecla_negra else 0)
            x_inicial_tecla = 2 if es_tecla_negra else 0
            self.keyboard_canvas.create_rectangle(x_inicial_tecla, y_pos_tecla, x_inicial_tecla + ancho_dibujo_tecla, y_pos_tecla + self.alto_fila_nota, fill=color_rect_tecla, outline=self.COLOR_TECLA_BORDE if not es_tecla_negra else self.COLOR_TECLA_NEGRA_BG, width=0.5, tags=f"key_{midi_val}")
            x_texto = (self.ancho_teclas_fijo - 5)
            self.keyboard_canvas.create_text(x_texto, y_pos_tecla + self.alto_fila_nota / 2, text=nombre_nota_display, anchor="e", font=("Segoe UI", 7), fill=self.COLOR_TEXTO_TECLAS, tags=f"key_text_{midi_val}")
            self.mapeo[nombre_nota_original_con_octava] = y_pos_tecla

    def dibujar_numeros_de_compas_en_regla(self):
        pixeles_por_compas_visual = self.pulsos_por_compas_visual * self.pixeles_por_pulso
        if pixeles_por_compas_visual <= 0: return
        num_compases_a_dibujar = self.scrollregion_width_solo_acordes // pixeles_por_compas_visual
        for i in range(int(num_compases_a_dibujar)):
            x_pos_inicio_bloque = i * pixeles_por_compas_visual
            self.ruler_canvas.create_line(x_pos_inicio_bloque, 0, x_pos_inicio_bloque, self.alto_regla_compases, fill=self.COLOR_LINEAS_FINAS, width=0.5, dash=(1,3))
            self.ruler_canvas.create_text(x_pos_inicio_bloque + pixeles_por_compas_visual / 2, self.alto_regla_compases / 2, text=str(i + 1), font=("Segoe UI", 8, "italic"), fill=self.COLOR_TEXTO_TECLAS, anchor="center")
        if num_compases_a_dibujar > 0:
            last_x = num_compases_a_dibujar * pixeles_por_compas_visual
            self.ruler_canvas.create_line(last_x, 0, last_x, self.alto_regla_compases, fill=self.COLOR_LINEAS_FINAS, width=0.5, dash=(1,3))

    def dibujar_acordes_mejorado(self, progresion_acordes_data, ritmo_progresion_data=None):
        if not progresion_acordes_data: return
        ritmo_a_usar = []
        if ritmo_progresion_data and len(ritmo_progresion_data) == len(progresion_acordes_data):
            try: ritmo_a_usar = [float(r) for r in ritmo_progresion_data]
            except ValueError: ritmo_a_usar = [1.0] * len(progresion_acordes_data)
        else: ritmo_a_usar = [1.0] * len(progresion_acordes_data)
        current_x = 0
        for i, elemento_acorde in enumerate(progresion_acordes_data):
            duracion_este_acorde_en_pulsos = ritmo_a_usar[i]
            ancho_visual_este_acorde = duracion_este_acorde_en_pulsos * self.pixeles_por_pulso
            if elemento_acorde == "0" or elemento_acorde == "N/A":
                current_x += ancho_visual_este_acorde
                continue
            notas_a_dibujar_con_octava = []
            try:
                if isinstance(elemento_acorde, list): notas_a_dibujar_con_octava = elemento_acorde
                elif isinstance(elemento_acorde, str):
                    cs = ChordSymbol(elemento_acorde)
                    pitches_obj = cs.pitches
                    if not pitches_obj: current_x += ancho_visual_este_acorde; continue
                    primera_nota_octava_base = 3
                    if pitches_obj[0].octave is None or pitches_obj[0].octave < primera_nota_octava_base -1:
                        temp_pitches_con_octava = []
                        current_octave_ref = primera_nota_octava_base
                        last_pitch_val = -1000
                        for p_obj_cs in cs.pitches:
                            p_temp = pitch.Pitch(p_obj_cs.name)
                            if p_temp.ps < last_pitch_val : current_octave_ref +=1
                            p_temp.octave = current_octave_ref
                            last_pitch_val = p_temp.ps
                            temp_pitches_con_octava.append(p_temp.nameWithOctave)
                        notas_a_dibujar_con_octava = temp_pitches_con_octava
                    else: notas_a_dibujar_con_octava = [p.nameWithOctave for p in pitches_obj]
                for nombre_nota_con_octava in notas_a_dibujar_con_octava:
                    if nombre_nota_con_octava in self.mapeo:
                        y_coord_superior_nota = self.mapeo[nombre_nota_con_octava]
                        try:
                            p_check = pitch.Pitch(nombre_nota_con_octava)
                            if not (self.midi_note_min <= p_check.midi <= self.midi_note_max): continue
                        except: continue
                        note_x1 = current_x
                        note_y1 = y_coord_superior_nota
                        note_x2 = current_x + ancho_visual_este_acorde
                        note_y2 = y_coord_superior_nota + self.alto_fila_nota
                        corner_radius = 3
                        self._create_rounded_rectangle(self.pianoroll_canvas, note_x1, note_y1, note_x2, note_y2, radius=corner_radius, fill=self.COLOR_NOTA_RELLENO, width=0)
            except Exception as e_acorde_viz: print(f"Error procesando/dibujando acorde '{elemento_acorde}': {e_acorde_viz}")
            current_x += ancho_visual_este_acorde

    def iniciar_cursor_reproduccion(self, total_duration_ms):
        self.total_duration_ms = total_duration_ms
        if self.total_duration_ms <= 0:
            print("WARN (PianoRoll): Duración total es 0 o negativa, no se inicia cursor.")
            self.is_playing = False
            return
        self.is_playing = True
        self.current_playback_time_ms = 0
        if self.playhead_line_pianoroll: self.pianoroll_canvas.delete(self.playhead_line_pianoroll)
        if self.playhead_line_ruler: self.ruler_canvas.delete(self.playhead_line_ruler)
        initial_x = 0
        self.playhead_line_pianoroll = self.pianoroll_canvas.create_line(initial_x, 0, initial_x, self.scrollregion_height_contenido_notas, fill=self.COLOR_PLAYHEAD, width=2, tags="playhead_pianoroll")
        self.playhead_line_ruler = self.ruler_canvas.create_line(initial_x, 0, initial_x, self.alto_regla_compases, fill=self.COLOR_PLAYHEAD, width=2, tags="playhead_ruler")
        if self.playback_update_job: self.after_cancel(self.playback_update_job)
        self._actualizar_cursor_reproduccion()

    def _actualizar_cursor_reproduccion(self):
        if not self.is_playing: return
        current_pygame_pos_ms = -1
        if pygame.mixer.get_init():
            current_pygame_pos_ms = pygame.mixer.music.get_pos()
            if current_pygame_pos_ms == -1 and self.is_playing: current_pygame_pos_ms = 0
        if current_pygame_pos_ms != -1:
            self.current_playback_time_ms = current_pygame_pos_ms
            progreso_fraccional = (self.current_playback_time_ms % self.total_duration_ms) / self.total_duration_ms if self.total_duration_ms > 0 else 0
            progreso_fraccional = min(max(0.0, progreso_fraccional), 1.0)
            duracion_total_pulsos = sum(float(d) for d in self.ritmo_progresion) if self.ritmo_progresion else 0
            ancho_total_progresion_px = duracion_total_pulsos * self.pixeles_por_pulso
            nueva_x_playhead = progreso_fraccional * ancho_total_progresion_px
            nueva_x_playhead = min(nueva_x_playhead, ancho_total_progresion_px if ancho_total_progresion_px > 0 else 0)
            if self.playhead_line_pianoroll: self.pianoroll_canvas.coords(self.playhead_line_pianoroll, nueva_x_playhead, 0, nueva_x_playhead, self.scrollregion_height_contenido_notas)
            if self.playhead_line_ruler: self.ruler_canvas.coords(self.playhead_line_ruler, nueva_x_playhead, 0, nueva_x_playhead, self.alto_regla_compases)
        if self.is_playing:
            if self.playback_update_job: self.after_cancel(self.playback_update_job)
            self.playback_update_job = self.after(30, self._actualizar_cursor_reproduccion)

    def detener_cursor_reproduccion(self):
        self.is_playing = False
        if self.playback_update_job:
            self.after_cancel(self.playback_update_job)
            self.playback_update_job = None
        print("DEBUG (PianoRoll): Cursor detenido (is_playing = False).")
