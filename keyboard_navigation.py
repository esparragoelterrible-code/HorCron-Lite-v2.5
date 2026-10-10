import tkinter as tk

class NavegadorTeclado:
    """Gestiona la matriz de navegación por teclado, atajos globales y control de modales."""

    def __init__(self, app):
        self.app = app
        self.grilla = getattr(app, "grilla", None)
        self.modo_edicion = False

        self.matriz_celdas = []
        self.pos_actual = [0, 0]

        # Referencias para toggle de modales
        self.v_config_ref = None
        self.v_ayuda_ref = None

    def _toggle_pantalla_completa(self):
        """Alterna entre pantalla completa y ventana normal."""
        estado_actual = self.app.attributes("-fullscreen")
        self.app.attributes("-fullscreen", not estado_actual)
        return "break"

    def construir_matriz(self):
        """Genera la representación en matriz tridimensional de los widgets CTkEntry."""
        self.grilla = getattr(self.app, "grilla", None)
        if not self.grilla or not hasattr(self.grilla, "entradas"):
            return

        dias = self.grilla.dias
        horas = self.grilla.horas

        self.matriz_celdas = []
        for h_idx, hora in enumerate(horas):
            fila = []
            for d_idx, dia in enumerate(dias):
                casilla = self.grilla.entradas.get((dia, hora))
                if casilla:
                    widget_entry = getattr(casilla, "_entry", casilla)
                    widget_entry.bind(
                        "<FocusIn>",
                        lambda e, f=h_idx, c=d_idx: self._sincronizar_foco(f, c),
                        add="+",
                    )
                fila.append(casilla)
            self.matriz_celdas.append(fila)

    def _sincronizar_foco(self, fila: int, col: int):
        self.pos_actual = [fila, col]

    def registrar_atajos(self):
        """Registra los eventos de teclado globales en la ventana principal."""
        # Flechas de dirección
        self.app.bind("<Up>", lambda e: self._mover_seleccion(-1, 0))
        self.app.bind("<Down>", lambda e: self._mover_seleccion(1, 0))
        self.app.bind("<Left>", lambda e: self._mover_seleccion(0, -1))
        self.app.bind("<Right>", lambda e: self._mover_seleccion(0, 1))

        # Edición y confirmación
        self.app.bind("<Return>", lambda e: self._mantiene_o_guarda())
        self.app.bind("<Escape>", lambda e: self._salir_modo_edicion())

        # Creación (F1 / Ctrl+T), Acordeón (F2) y Rotación de pestañas (Ctrl+, / Ctrl+.)
        self.app.bind("<F1>", lambda e: self._crear_nueva_pestana())
        self.app.bind("<F2>", lambda e: self._toggle_horarios_guardados())
        self.app.bind("<Control-t>", lambda e: self._crear_nueva_pestana())
        self.app.bind("<Control-T>", lambda e: self._crear_nueva_pestana())
        self.app.bind("<Control-comma>", lambda e: self._cambiar_pestana(-1))
        self.app.bind("<Control-period>", lambda e: self._cambiar_pestana(1))

        # Atajos de Acción sobre celdas e Inspector de Notas
        self.app.bind("<Control-n>", lambda e: self._toggle_inspector_notas())
        self.app.bind("<Control-N>", lambda e: self._toggle_inspector_notas())
        self.app.bind("<Control-l>", lambda e: self._limpiar_celda_actual())
        self.app.bind("<Control-L>", lambda e: self._limpiar_celda_actual())

        # EXPORTACIÓN (Ctrl + M, Ctrl + P, Ctrl + E)
        self.app.bind("<Control-m>", lambda e: self._abrir_exportar())
        self.app.bind("<Control-M>", lambda e: self._abrir_exportar())
        self.app.bind("<Control-p>", lambda e: self._exportar_pdf())
        self.app.bind("<Control-P>", lambda e: self._exportar_pdf())
        self.app.bind("<Control-e>", lambda e: self._exportar_ics())
        self.app.bind("<Control-E>", lambda e: self._exportar_ics())

        # CONFIGURACIÓN (Ctrl + O)
        self.app.bind("<Control-o>", lambda e: self._abrir_config())
        self.app.bind("<Control-O>", lambda e: self._abrir_config())

        # AYUDA DE ATAJOS (Ctrl + H)
        self.app.bind("<Control-h>", lambda e: self._abrir_ayuda_atajos())
        self.app.bind("<Control-H>", lambda e: self._abrir_ayuda_atajos())

        # PANTALLA COMPLETA (F11)
        self.app.bind("<F11>", lambda e: self._toggle_pantalla_completa())

        self.app.after(100, self._enfocar_inicial)

    # ==========================================
    # LÓGICA DE PESTAÑAS Y ACORDEÓN
    # ==========================================

    def _toggle_horarios_guardados(self):
        if hasattr(self.app, "gestor_guardados") and self.app.gestor_guardados:
            self.app.gestor_guardados.toggle_desplegable()
        return "break"

    def _cambiar_pestana(self, direccion: int):
        pestanas = getattr(self.app, "pestanas_abiertas", [])
        activo_actual = getattr(self.app, "cronograma_actual", None)

        if not pestanas or len(pestanas) <= 1 or not activo_actual:
            return "break"

        try:
            idx_actual = pestanas.index(activo_actual)
            nuevo_idx = (idx_actual + direccion) % len(pestanas)
            siguiente_cronograma = pestanas[nuevo_idx]

            if hasattr(self.app, "cb_cambiar_cronograma"):
                self.app.cb_cambiar_cronograma(siguiente_cronograma)
        except ValueError:
            pass

        return "break"

    def _crear_nueva_pestana(self):
        if hasattr(self.app, "cb_crear_cronograma"):
            self.app.cb_crear_cronograma()
        return "break"

    # ==========================================
    # LÓGICA DE EXPORTACIÓN Y MODALES
    # ==========================================

    def _abrir_exportar(self):
        if hasattr(self.app, "abrir_menu_exportar"):
            self.app.abrir_menu_exportar()
        return "break"

    def _exportar_pdf(self):
        if hasattr(self.app, "_exportar_directo_pdf"):
            self.app._exportar_directo_pdf()
        return "break"

    def _exportar_ics(self):
        if hasattr(self.app, "_exportar_directo_ics"):
            self.app._exportar_directo_ics()
        return "break"

    def _abrir_ayuda_atajos(self):
        if self.v_ayuda_ref is not None and self.v_ayuda_ref.winfo_exists():
            self.v_ayuda_ref.destroy()
            self.v_ayuda_ref = None
            self.app.focus_set()
        else:
            try:
                from shortcuts_modal import VentanaAtajosTeclado
                self.v_ayuda_ref = VentanaAtajosTeclado(self.app)
            except Exception as e:
                print(f"[Error Modal Atajos]: {e}")
        return "break"

    def _abrir_config(self):
        if self.v_config_ref is not None and self.v_config_ref.winfo_exists():
            self.v_config_ref.destroy()
            self.v_config_ref = None
            self.app.focus_set()
        else:
            try:
                from config_window import VentanaConfiguracion
                self.v_config_ref = VentanaConfiguracion(self.app)

                self.v_config_ref.bind("<Control-o>", lambda e: self._cerrar_config_directo())
                self.v_config_ref.bind("<Control-O>", lambda e: self._cerrar_config_directo())
            except ImportError:
                if hasattr(self.app, "mostrar_mensaje_estado"):
                    self.app.mostrar_mensaje_estado("⚠ Módulo de configuración desactivado", "#E69138")
        return "break"

    def _cerrar_config_directo(self):
        if self.v_config_ref is not None and self.v_config_ref.winfo_exists():
            self.v_config_ref.destroy()
            self.v_config_ref = None
            self.app.focus_set()
        return "break"

    # ==========================================
    # NAVEGACIÓN DE GRILLA Y EDICIÓN
    # ==========================================

    def _enfocar_inicial(self):
        self.construir_matriz()
        if self.matriz_celdas and len(self.matriz_celdas) > 0:
            primera_celda = self.matriz_celdas[0][0]
            if primera_celda:
                primera_celda.focus_set()

    def _mover_seleccion(self, dfila: int, dcol: int):
        if not self.matriz_celdas:
            self.construir_matriz()

        max_filas = len(self.matriz_celdas)
        max_cols = len(self.matriz_celdas[0]) if max_filas > 0 else 0

        if max_filas == 0 or max_cols == 0:
            return "break"

        if self.modo_edicion and dcol != 0:
            return

        nueva_fila = max(0, min(max_filas - 1, self.pos_actual[0] + dfila))
        nueva_col = max(0, min(max_cols - 1, self.pos_actual[1] + dcol))

        self.pos_actual = [nueva_fila, nueva_col]
        celda_destino = self.matriz_celdas[nueva_fila][nueva_col]

        if celda_destino:
            self.modo_edicion = False
            celda_destino.focus_set()

            if hasattr(self.app, "grilla"):
                dia = self.app.grilla.dias[nueva_col]
                hora = self.app.grilla.horas[nueva_fila]
                self.app.al_seleccionar_celda(dia, hora)

        return "break"

    def _mantiene_o_guarda(self):
        if not self.modo_edicion:
            self.modo_edicion = True
        else:
            self.app.guardar_datos()
            self.modo_edicion = False
            self.app.focus_set()
        return "break"

    def _salir_modo_edicion(self):
        self.modo_edicion = False
        self.app.focus_set()
        return "break"

    def _toggle_inspector_notas(self):
        if hasattr(self.app, "gestor_notas"):
            if self.app.gestor_notas.panel_desplegado:
                self.app.gestor_notas.alternar_panel()
                self.app.focus_set()
            else:
                self.app.gestor_notas.alternar_panel()
                if hasattr(self.app.gestor_notas, "txt_notas"):
                    self.app.gestor_notas.txt_notas.focus_set()
        return "break"

    def _limpiar_celda_actual(self):
        """Limpia inmediatamente el contenido de la celda activa en O(1)."""
        if not self.matriz_celdas:
            return "break"

        fila, col = self.pos_actual
        if 0 <= fila < len(self.matriz_celdas) and 0 <= col < len(self.matriz_celdas[0]):
            celda = self.matriz_celdas[fila][col]
            if celda:
                celda.delete(0, tk.END)
                if hasattr(self.app, "reaplicar_colores_grilla"):
                    self.app.reaplicar_colores_grilla()

        return "break"