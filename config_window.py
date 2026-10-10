import customtkinter as tk  # type: ignore
from typing import Dict, Any, List
from config import cargar_configuracion, guardar_configuracion

class VentanaConfiguracion(tk.CTkToplevel):
    """Ventana para la gestión persistente de preferencias de la aplicación."""

    def __init__(self, parent: tk.CTk) -> None:
        super().__init__(parent)

        self.title("Configuración y Personalización ⚙️")
        self.geometry("500x650")
        self.resizable(False, False)

        # Cargar preferencias reales
        self.config_data: Dict[str, Any] = cargar_configuracion()
        self.categorias_locales: Dict[str, Any] = self.config_data.get("categorias", {})

        # Control de selección en la lista
        self.indice_seleccionado: int = -1
        self.items_widgets: List[tk.CTkFrame] = []

        # Configuración de foco sobre la ventana modal
        self.attributes("-topmost", True)
        self.grab_set()
        self.focus_force()

        # Protocolo de cierre seguro (Revertir vista previa si se cancela)
        self.protocol("WM_DELETE_WINDOW", self.destruir_o_cancelar)

        # Título principal
        lbl_titulo = tk.CTkLabel(
            self,
            text="Preferencias del Sistema",
            font=("Segoe UI", 18, "bold"),
            text_color="#89B4FA",
        )
        lbl_titulo.pack(pady=(20, 10))

        # Contenedor desplazable de opciones
        self.frame_contenido = tk.CTkScrollableFrame(self)
        self.frame_contenido.pack(fill="both", expand=True, padx=15, pady=10)

        # Construcción de secciones de interfaz
        self._crear_seccion_apariencia()
        self._crear_seccion_categorias()
        self._crear_seccion_notificaciones()

        # --- BINDINGS DE ATAJOS POR TECLADO ---
        self.bind("<F1>", lambda e: self._rotar_opcion_tema())
        self.bind("<F2>", lambda e: self._rotar_opcion_reloj())
        self.bind("<F3>", lambda e: self._toggle_indicador_vacio())
        self.bind("<F4>", lambda e: self._enfocar_o_salir_creador())
        self.bind("<F5>", lambda e: self._desplegar_menu_colores())
        self.bind("<F6>", lambda e: self._toggle_notificaciones())
        
        # Tecla V local
        self.bind("<v>", self._manejador_tecla_v)
        self.bind("<V>", self._manejador_tecla_v)

        # Controles de selección y borrado
        self.bind("<Control-x>", lambda e: self._activar_modo_seleccion())
        self.bind("<Control-X>", lambda e: self._activar_modo_seleccion())
        self.bind("<Control-z>", lambda e: self._borrar_categoria_seleccionada())
        self.bind("<Control-Z>", lambda e: self._borrar_categoria_seleccionada())

        # Navegación y cierre
        self.bind("<Down>", lambda e: self._desplazar_o_navegar(1))
        self.bind("<Up>", lambda e: self._desplazar_o_navegar(-1))
        self.bind("<Escape>", lambda e: self.destruir_o_cancelar())

        # Botón principal de guardado
        btn_guardar = tk.CTkButton(
            self,
            text="Guardar Preferencias (V)",
            command=self.guardar_preferencias,
            fg_color="#A6E3A1",
            text_color="#11111B",
            hover_color="#94E2D5",
            font=("Segoe UI", 12, "bold"),
            height=38,
        )
        btn_guardar.pack(pady=15)

    def _manejador_tecla_v(self, event: Any) -> str:
        foco_actual = self.focus_get()
        if isinstance(foco_actual, (tk.CTkEntry, tk.CTkTextbox)):
            return ""
        self.guardar_preferencias()
        return "break"

    def _crear_seccion_apariencia(self) -> None:
        lbl_sec = tk.CTkLabel(
            self.frame_contenido,
            text="🎨 Apariencia",
            font=("Segoe UI", 14, "bold"),
        )
        lbl_sec.pack(anchor="w", padx=10, pady=(10, 5))

        # Tema
        frame_tema = tk.CTkFrame(self.frame_contenido, fg_color="transparent")
        frame_tema.pack(fill="x", padx=10, pady=(0, 10))
        tk.CTkLabel(frame_tema, text="Tema de Interfaz:", font=("Segoe UI", 12)).pack(side="left")
        
        self.opciones_tema = ["Dark", "Light", "System"]
        self.option_tema = tk.CTkOptionMenu(frame_tema, values=self.opciones_tema, command=self._al_cambiar_tema)
        self.option_tema.set(self.config_data.get("tema", "Dark"))
        self.option_tema.pack(side="right")
        tk.CTkLabel(frame_tema, text="(F1) ", font=("Consolas", 11, "bold"), text_color="#89B4FA").pack(side="right", padx=(0, 5))

        # Hora
        frame_fmt_hora = tk.CTkFrame(self.frame_contenido, fg_color="transparent")
        frame_fmt_hora.pack(fill="x", padx=10, pady=(0, 10))
        tk.CTkLabel(frame_fmt_hora, text="Formato de Reloj:", font=("Segoe UI", 12)).pack(side="left")
        
        self.opciones_hora = ["24h", "12h"]
        self.option_hora = tk.CTkOptionMenu(frame_fmt_hora, values=self.opciones_hora, command=self._al_cambiar_formato_hora, width=110)
        self.option_hora.set(self.config_data.get("formato_hora", "24h"))
        self.option_hora.pack(side="right")
        tk.CTkLabel(frame_fmt_hora, text="(F2) ", font=("Consolas", 11, "bold"), text_color="#89B4FA").pack(side="right", padx=(0, 5))

        # Switch Vacío (Vista previa temporal)
        self.switch_vacio = tk.CTkSwitch(
            self.frame_contenido,
            text="(F3) Mostrar 'vacío...' en celdas sin tareas",
            progress_color="#89B4FA",
            font=("Segoe UI", 12),
            command=self._al_cambiar_indicador_vacio,
        )
        if self.config_data.get("mostrar_indicador_vacio", True):
            self.switch_vacio.select()
        else:
            self.switch_vacio.deselect()
        self.switch_vacio.pack(anchor="w", padx=10, pady=(5, 15))

    def _rotar_opcion_tema(self) -> str:
        val = self.option_tema.get()
        if val in self.opciones_tema:
            idx = (self.opciones_tema.index(val) + 1) % len(self.opciones_tema)
            self.option_tema.set(self.opciones_tema[idx])
            self._al_cambiar_tema(self.opciones_tema[idx])
        return "break"

    def _rotar_opcion_reloj(self) -> str:
        val = self.option_hora.get()
        if val in self.opciones_hora:
            idx = (self.opciones_hora.index(val) + 1) % len(self.opciones_hora)
            self.option_hora.set(self.opciones_hora[idx])
            self._al_cambiar_formato_hora(self.opciones_hora[idx])
        return "break"

    def _toggle_indicador_vacio(self) -> str:
        if self.switch_vacio.get() == 1:
            self.switch_vacio.deselect()
        else:
            self.switch_vacio.select()
        self._al_cambiar_indicador_vacio()
        return "break"

    def _al_cambiar_indicador_vacio(self) -> None:
        """Actualiza la vista previa del indicador en la grilla sin alterar el disco todavía."""
        self.config_data["mostrar_indicador_vacio"] = bool(self.switch_vacio.get())
        if hasattr(self.master, "grilla") and hasattr(self.master.grilla, "actualizar_placeholders_con_valor"):
            self.master.grilla.actualizar_placeholders_con_valor(self.config_data["mostrar_indicador_vacio"])

    def _enfocar_o_salir_creador(self) -> str:
        if self.focus_get() == self.entry_palabra:
            self.focus_set()
        else:
            self._limpiar_seleccion_lista()
            self.entry_palabra.focus_set()
            self.entry_palabra.select_range(0, tk.END)
        return "break"

    def _desplegar_menu_colores(self) -> str:
        self.option_color.focus_set()
        if hasattr(self.option_color, "_dropdown_menu") and self.option_color._dropdown_menu:
            self.option_color._dropdown_menu.post(
                self.option_color.winfo_rootx(),
                self.option_color.winfo_rooty() + self.option_color.winfo_height()
            )
        return "break"

    def _rotar_color(self, direccion: int = 1) -> str:
        if self.focus_get() == self.option_color:
            actual = self.option_color.get()
            if actual in self.lista_colores:
                idx = (self.lista_colores.index(actual) + direccion) % len(self.lista_colores)
                self.option_color.set(self.lista_colores[idx])
            return "break"
        return ""

    def _desplazar_o_navegar(self, direccion: int) -> str:
        if self.focus_get() == self.option_color:
            return self._rotar_color(direccion)
        if self.indice_seleccionado != -1 and self.items_widgets:
            self.indice_seleccionado = (self.indice_seleccionado + direccion) % len(self.items_widgets)
            self._actualizar_resaltado_lista()
            return "break"
        if hasattr(self.frame_contenido, "_parent_canvas"):
            self.frame_contenido._parent_canvas.yview_scroll(direccion * 4, "units")
        return "break"

    def _al_cambiar_tema(self, nuevo_tema: str) -> None:
        tk.set_appearance_mode(nuevo_tema.lower())
        if hasattr(self.master, "actualizar_tema"):
            self.master.actualizar_tema()

    def _al_cambiar_formato_hora(self, nuevo_formato: str) -> None:
        self.config_data["formato_hora"] = nuevo_formato
        if hasattr(self.master, "actualizar_formato_hora"):
            self.master.actualizar_formato_hora()

    def _crear_seccion_categorias(self) -> None:
        frame_header = tk.CTkFrame(self.frame_contenido, fg_color="transparent")
        frame_header.pack(fill="x", padx=10, pady=(10, 5))

        tk.CTkLabel(frame_header, text="🏷 Categorías y Colores", font=("Segoe UI", 14, "bold")).pack(side="left")
        tk.CTkLabel(frame_header, text=" (F4: escribir | F5: color)", font=("Consolas", 11, "bold"), text_color="#89B4FA").pack(side="left")

        frame_input = tk.CTkFrame(self.frame_contenido, fg_color="transparent")
        frame_input.pack(fill="x", padx=10, pady=5)

        self.entry_palabra = tk.CTkEntry(frame_input, placeholder_text="Ej: Gimnasio... (Enter)", width=175)
        self.entry_palabra.pack(side="left", padx=(0, 5))
        self.entry_palabra.bind("<Return>", lambda e: self._agregar_categoria())
        self.entry_palabra.bind("<F5>", lambda e: self._desplegar_menu_colores())

        self.lista_colores = ["Verde", "Azul", "Morado", "Naranja", "Rojo", "Cian", "Rosado", "Amarillo", "Turquesa", "Gris"]
        self.option_color = tk.CTkOptionMenu(frame_input, values=self.lista_colores, width=120)
        self.option_color.pack(side="left", padx=5)
        self.option_color.bind("<Return>", lambda e: self._agregar_categoria())
        self.option_color.bind("<F5>", lambda e: self._desplegar_menu_colores())

        btn_agregar = tk.CTkButton(
            frame_input, text="+", width=35,
            fg_color="#89B4FA", text_color="#11111B", hover_color="#B4BEFE",
            command=self._agregar_categoria,
        )
        btn_agregar.pack(side="left", padx=5)

        self.frame_lista_cat = tk.CTkFrame(self.frame_contenido)
        self.frame_lista_cat.pack(fill="x", padx=10, pady=(5, 5))
        self._renderizar_lista_categorias()

        tk.CTkLabel(
            self.frame_contenido,
            text="(Ctrl+X: seleccionar lista | Ctrl+Z: borrar seleccionada)",
            font=("Consolas", 10, "bold"),
            text_color="#89B4FA",
        ).pack(anchor="w", padx=15, pady=(0, 15))

    def _activar_modo_seleccion(self) -> str:
        if self.items_widgets:
            self.focus_set()
            self.indice_seleccionado = 0
            self._actualizar_resaltado_lista()
        return "break"

    def _actualizar_resaltado_lista(self) -> None:
        for idx, frame in enumerate(self.items_widgets):
            if idx == self.indice_seleccionado:
                frame.configure(fg_color="#363a4f", border_width=0)
            else:
                frame.configure(fg_color="transparent", border_width=0)

    def _limpiar_seleccion_lista(self) -> None:
        self.indice_seleccionado = -1
        self._actualizar_resaltado_lista()

    def _borrar_categoria_seleccionada(self) -> str:
        if self.indice_seleccionado != -1 and self.categorias_locales:
            claves = list(self.categorias_locales.keys())
            if 0 <= self.indice_seleccionado < len(claves):
                self._eliminar_categoria(claves[self.indice_seleccionado])
            self.entry_palabra.focus_set()
            return "break"
        return ""

    def _renderizar_lista_categorias(self) -> None:
        for widget in self.frame_lista_cat.winfo_children():
            widget.destroy()

        self.items_widgets.clear()
        for palabra, colores in list(self.categorias_locales.items()):
            color_muestra = colores.get("fondo", "#313244") if isinstance(colores, dict) else colores

            f_item = tk.CTkFrame(self.frame_lista_cat, height=32, corner_radius=6)
            f_item.pack(fill="x", padx=5, pady=3)
            self.items_widgets.append(f_item)

            tk.CTkLabel(f_item, text=f"• {palabra}", font=("Segoe UI", 11, "bold")).pack(side="left", padx=10)
            
            btn_del = tk.CTkButton(
                f_item, text="✕", width=24, height=24,
                fg_color="#F38BA8", text_color="#11111B", hover_color="#EBA0AC",
                command=lambda p=palabra: self._eliminar_categoria(p),
            )
            btn_del.pack(side="right", padx=5)
            tk.CTkFrame(f_item, fg_color=color_muestra, width=20, height=20, corner_radius=10).pack(side="right", padx=5)

        self._actualizar_resaltado_lista()

    def _agregar_categoria(self) -> None:
        palabra = self.entry_palabra.get().strip().lower()
        color_nombre = self.option_color.get()
        mapa_colores = {
            "Verde": {"fondo": "#2e5b31", "borde": "#2E7D32"},
            "Azul": {"fondo": "#1e3a5f", "borde": "#1565C0"},
            "Morado": {"fondo": "#5e1e47", "borde": "#AD1457"},
            "Naranja": {"fondo": "#7a521e", "borde": "#F57F17"},
            "Rojo": {"fondo": "#5f1e1e", "borde": "#C62828"},
            "Cian": {"fondo": "#1e525f", "borde": "#00838F"},
            "Rosado": {"fondo": "#5f1e43", "borde": "#C2185B"},
            "Amarillo": {"fondo": "#5f561e", "borde": "#FBC02D"},
            "Turquesa": {"fondo": "#1e5f4e", "borde": "#00695C"},
            "Gris": {"fondo": "#3a3b4c", "borde": "#6C7086"},
        }
        if palabra and palabra not in self.categorias_locales:
            self.categorias_locales[palabra] = mapa_colores.get(color_nombre, {"fondo": "#313244", "borde": "#45475A"})
            self.entry_palabra.delete(0, "end")
            self._renderizar_lista_categorias()

    def _eliminar_categoria(self, palabra: str) -> None:
        if palabra in self.categorias_locales:
            del self.categorias_locales[palabra]
            self._limpiar_seleccion_lista()
            self._renderizar_lista_categorias()

    def _crear_seccion_notificaciones(self) -> None:
        tk.CTkLabel(self.frame_contenido, text="🔔 Notificaciones", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        self.switch_notificaciones = tk.CTkSwitch(
            self.frame_contenido,
            text="(F6) Activar notificaciones del sistema",
            progress_color="#89B4FA",
            font=("Segoe UI", 12),
        )
        if self.config_data.get("notificaciones_activas", True):
            self.switch_notificaciones.select()
        else:
            self.switch_notificaciones.deselect()
        self.switch_notificaciones.pack(anchor="w", padx=10, pady=5)

    def _toggle_notificaciones(self) -> str:
        if self.switch_notificaciones.get() == 1:
            self.switch_notificaciones.deselect()
        else:
            self.switch_notificaciones.select()
        return "break"

    def destruir_o_cancelar(self) -> None:
        """Restaura los placeholders reales desde el disco si se cancela la ventana."""
        if hasattr(self.master, "grilla") and hasattr(self.master.grilla, "actualizar_placeholders"):
            self.master.grilla.actualizar_placeholders()
        if self.master and hasattr(self.master, "focus_set"):
            self.master.focus_set()
        self.destroy()

    def guardar_preferencias(self) -> None:
        """Almacena el estado completo de configuración en disco de forma definitiva."""
        self.config_data["tema"] = self.option_tema.get()
        self.config_data["formato_hora"] = self.option_hora.get()
        self.config_data["mostrar_indicador_vacio"] = bool(self.switch_vacio.get())
        self.config_data["categorias"] = self.categorias_locales
        self.config_data["notificaciones_activas"] = bool(self.switch_notificaciones.get())

        guardar_configuracion(self.config_data)

        if hasattr(self.master, "actualizar_tema"):
            self.master.actualizar_tema()
        if hasattr(self.master, "actualizar_formato_hora"):
            self.master.actualizar_formato_hora()
        if hasattr(self.master, "grilla"):
            self.master.grilla.actualizar_placeholders()
        if hasattr(self.master, "reaplicar_colores_grilla"):
            self.master.reaplicar_colores_grilla()

        if self.master and hasattr(self.master, "focus_set"):
            self.master.focus_set()
        self.destroy()