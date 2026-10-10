import json
import os
import customtkinter as ctk
from typing import Callable, Optional, List, Tuple
from config import SUGERENCIAS_NOTAS, cargar_configuracion
from persistence import cargar_json_completo

class GestorInspectorNotas:
    """Maneja el panel inferior desplegable de notas asociadas a cada celda."""

    def __init__(
        self,
        frame_master: ctk.CTk,
        obtener_cronograma_actual: Callable[[], str],
        obtener_ruta_json: Callable[[], str],
        formatear_hora_fn: Callable[[str, str], str],
    ):
        self.frame_master = frame_master
        self.obtener_cronograma_actual = obtener_cronograma_actual
        self.obtener_ruta_json = obtener_ruta_json
        self.formatear_hora_fn = formatear_hora_fn

        self.celda_activa_key: Optional[str] = None
        self.texto_tarea_actual: str = ""
        self.hora_formateada_actual: str = ""
        self.panel_desplegado: bool = False
        self.es_placeholder: bool = False

        self._construir_ui()

    def _construir_ui(self):
        self.frame_container = ctk.CTkFrame(
            self.frame_master, fg_color=("#D1D5DB", "#1E1E2E"), corner_radius=8
        )
        self.frame_container.pack(fill="x", padx=10, pady=(2, 5))

        self.frame_header = ctk.CTkFrame(
            self.frame_container, fg_color="transparent", height=32
        )
        self.frame_header.pack(fill="x", padx=10, pady=5)

        self.frame_titulos = ctk.CTkFrame(self.frame_header, fg_color="transparent")
        self.frame_titulos.pack(side="left", fill="x", expand=True)

        self.lbl_titulo_seccion = ctk.CTkLabel(
            self.frame_titulos,
            text="Inspector de Notas",
            font=("Segoe UI", 12, "bold"),
            text_color=("#1F2937", "#CDD6F4"),
        )
        self.lbl_titulo_seccion.pack(side="left", padx=(0, 10))

        self.lbl_info = ctk.CTkLabel(
            self.frame_titulos,
            text="📌 Selecciona una casilla para ver o añadir notas",
            font=("Segoe UI", 11),
            text_color=("#1D4ED8", "#89B4FA"),
        )
        self.lbl_info.pack(side="left")

        self.frame_acciones = ctk.CTkFrame(self.frame_header, fg_color="transparent")
        self.frame_acciones.pack(side="right", padx=(5, 0))

        self.btn_toggle = ctk.CTkButton(
            self.frame_acciones,
            text="▲ Expandir Notas",
            width=120,
            height=26,
            fg_color=("#9CA3AF", "#45475A"),
            text_color=("#1F2937", "#CDD6F4"),
            hover_color=("#8F949D", "#585B70"),
            font=("Segoe UI", 11, "bold"),
            command=self.alternar_panel,
        )
        self.btn_toggle.pack(anchor="e")

        self.frame_contenido = ctk.CTkFrame(
            self.frame_container, fg_color="transparent"
        )

        self.lbl_instrucciones = ctk.CTkLabel(
            self.frame_contenido,
            text="Detalles / Instrucciones de la casilla activa:",
            font=("Segoe UI", 11, "italic"),
            text_color=("#4B5563", "#A6ADC8"),
        )
        self.lbl_instrucciones.pack(anchor="w", pady=(0, 3))

        self.txt_notas = ctk.CTkTextbox(
            self.frame_contenido,
            height=80,
            corner_radius=6,
            fg_color=("#FFFFFF", "#181825"),
            text_color=("#111827", "#CDD6F4"),
            font=("Segoe UI", 11),
        )
        self.txt_notas.pack(fill="x", expand=True)

        self.txt_notas.bind("<FocusIn>", self._al_enfocar_texto)
        self.txt_notas.bind("<FocusOut>", self._al_desenfocar_texto)

    def alternar_panel(self):
        """Muestra u oculta la caja de texto del inspector de notas."""
        if self.panel_desplegado:
            self.frame_contenido.pack_forget()
            self.btn_toggle.configure(text="▲ Expandir Notas")
            self.panel_desplegado = False
        else:
            self.frame_contenido.pack(fill="x", padx=10, pady=(0, 10))
            self.btn_toggle.configure(text="▼ Ocultar Notas")
            self.panel_desplegado = True

    def _obtener_sugerencia_placeholder(self, texto_tarea: str, hora_str: str) -> str:
        tarea_lower = texto_tarea.lower() if texto_tarea else ""

        if any(p in tarea_lower for p in ["ejercicio", "gym", "rutina", "entreno", "deporte", "correr"]):
            plantilla = SUGERENCIAS_NOTAS.get("ejercicio", "")
        elif any(p in tarea_lower for p in ["tarea", "estudio", "apunte", "revisar", "deber", "proyecto"]):
            plantilla = SUGERENCIAS_NOTAS.get("tarea", "")
        elif any(p in tarea_lower for p in ["jugar", "juego", "recreación", "recreacion", "hobby", "distraer", "ocio"]):
            plantilla = SUGERENCIAS_NOTAS.get("recreación", "")
        else:
            plantilla = SUGERENCIAS_NOTAS.get("general", "")

        try:
            return plantilla.format(
                hora=hora_str,
                hora_mas_25=f"{hora_str} (+25m)",
                hora_mas_30=f"{hora_str} (+30m)",
            )
        except Exception:
            return f"{hora_str}: Detalle o instrucción de la casilla..."

    def _mostrar_placeholder(self):
        sugerencia = self._obtener_sugerencia_placeholder(
            self.texto_tarea_actual, self.hora_formateada_actual
        )
        self.txt_notas.delete("1.0", ctk.END)
        self.txt_notas.configure(text_color="gray50")
        self.txt_notas.insert("1.0", sugerencia)
        self.es_placeholder = True

    def _al_enfocar_texto(self, event=None):
        if self.es_placeholder:
            self.txt_notas.delete("1.0", ctk.END)
            self.txt_notas.configure(text_color=("#111827", "#CDD6F4"))
            self.es_placeholder = False

    def _al_desenfocar_texto(self, event=None):
        contenido = self.txt_notas.get("1.0", ctk.END).strip()
        if not contenido:
            self._mostrar_placeholder()

    def cargar_nota_celda(self, dia: str, hora: str, texto_tarea: str, formato_hora: str):
        self.celda_activa_key = f"{dia}_{hora}"
        self.texto_tarea_actual = texto_tarea or ""
        self.hora_formateada_actual = self.formatear_hora_fn(hora, formato_hora)

        self.lbl_info.configure(
            text=f"📌 {dia} {self.hora_formateada_actual} | {self.texto_tarea_actual or 'Sin tarea asignada'}"
        )

        ruta = self.obtener_ruta_json()
        datos = cargar_json_completo(ruta)
        c_act = self.obtener_cronograma_actual()
        
        nota_guardada = (
            datos.get("_notas", {})
            .get(c_act, {})
            .get(self.celda_activa_key, "")
        )

        self.txt_notas.delete("1.0", ctk.END)

        if nota_guardada and nota_guardada.strip():
            self.txt_notas.configure(text_color=("#111827", "#CDD6F4"))
            self.txt_notas.insert("1.0", nota_guardada)
            self.es_placeholder = False
        else:
            self._mostrar_placeholder()

    def obtener_nota_actual(self) -> Tuple[Optional[str], str]:
        if not self.celda_activa_key or self.es_placeholder:
            return self.celda_activa_key, ""
        return self.celda_activa_key, self.txt_notas.get("1.0", ctk.END).strip()


class EditarCalendarioModal(ctk.CTkToplevel):
    """Ventana modal para renombrar una pestaña y cambiar su color identificador."""

    def __init__(self, parent, nombre_actual: str, color_actual: str, callback_guardar: Callable[[str, str], None]):
        super().__init__(parent)
        self.title("Editar Calendario")
        self.geometry("320x220")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self.callback_guardar = callback_guardar
        self.color_seleccionado = color_actual or "#89B4FA"

        self.label_nombre = ctk.CTkLabel(
            self, text="Nombre del Calendario:", font=("Segoe UI", 12, "bold")
        )
        self.label_nombre.pack(pady=(15, 5))

        self.entry_nombre = ctk.CTkEntry(self, width=240)
        self.entry_nombre.insert(0, nombre_actual)
        self.entry_nombre.pack(pady=5)
        self.entry_nombre.focus_set()

        self.label_color = ctk.CTkLabel(
            self, text="Color de la Pestaña:", font=("Segoe UI", 11, "bold")
        )
        self.label_color.pack(pady=(10, 3))

        self.frame_colores = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_colores.pack(pady=5)

        colores_sugeridos = [
            "#89B4FA", "#A6E3A1", "#F38BA8", "#FAB387", "#CBA6F7", "#74C7EC", "#5951A8"
        ]
        for col in colores_sugeridos:
            btn_col = ctk.CTkButton(
                self.frame_colores,
                text="",
                width=24,
                height=24,
                fg_color=col,
                hover_color=col,
                command=lambda c=col: self._seleccionar_color(c),
            )
            btn_col.pack(side="left", padx=3)

        self.btn_guardar = ctk.CTkButton(
            self,
            text="Guardar Cambios",
            command=self._confirmar,
            fg_color="#A6E3A1",
            text_color="#11111B",
            hover_color="#94E2D5",
            font=("Segoe UI", 11, "bold"),
        )
        self.btn_guardar.pack(pady=(15, 10))

        self.bind("<Return>", lambda e: self._confirmar())
        self.bind("<Escape>", lambda e: self.destroy())

    def _seleccionar_color(self, color_hex: str):
        self.color_seleccionado = color_hex

    def _confirmar(self):
        nuevo_nombre = self.entry_nombre.get().strip()
        if nuevo_nombre:
            self.callback_guardar(nuevo_nombre, self.color_seleccionado)
            self.destroy()


class GestorPestanasPuras:
    """Renderiza las pestañas superiores y gestiona sus eventos de clic/edición/cierre."""

    def __init__(
        self,
        frame_master: ctk.CTk,
        lista_cronogramas: List[str],
        cronograma_actual: str,
        on_cambiar_cb: Callable[[str], None],
        on_crear_cb: Callable[[], None],
        on_eliminar_cb: Callable[[str], None],
        on_editar_cb: Optional[Callable[[str], None]] = None,
    ):
        self.frame_master = frame_master
        self.lista_cronogramas = lista_cronogramas
        self.cronograma_actual = cronograma_actual
        self.on_cambiar_cb = on_cambiar_cb
        self.on_crear_cb = on_crear_cb
        self.on_eliminar_cb = on_eliminar_cb
        self.on_editar_cb = on_editar_cb

        self.contenedor_pestanas = None
        self._construir_base()

    def _construir_base(self):
        self.frame_bar = ctk.CTkFrame(
            self.frame_master,
            fg_color=("#D1D5DB", "#1E1E2E"),
            height=42,
            corner_radius=8,
        )
        self.frame_bar.pack(fill="x", padx=10, pady=(10, 5))

        self.btn_add = ctk.CTkButton(
            self.frame_bar,
            text="+",
            width=32,
            height=28,
            fg_color="#A6E3A1",
            text_color="#11111B",
            hover_color="#94E2D5",
            font=("Segoe UI", 14, "bold"),
            command=self.on_crear_cb,
        )
        self.btn_add.pack(side="right", padx=8)

    def renderizar(self, lista_cronogramas: List[str], cronograma_actual: str):
        self.lista_cronogramas = lista_cronogramas
        self.cronograma_actual = cronograma_actual

        if self.contenedor_pestanas and self.contenedor_pestanas.winfo_exists():
            self.contenedor_pestanas.destroy()

        if len(self.lista_cronogramas) > 5:
            self.contenedor_pestanas = ctk.CTkScrollableFrame(
                self.frame_bar,
                orientation="horizontal",
                fg_color="transparent",
                height=32,
            )
        else:
            self.contenedor_pestanas = ctk.CTkFrame(
                self.frame_bar, fg_color="transparent", height=32
            )

        self.contenedor_pestanas.pack(
            side="left", fill="both", expand=True, padx=5, pady=2
        )

        cfg = cargar_configuracion()
        colores_dict = cfg.get("colores_pestanas", {})

        for nombre in self.lista_cronogramas:
            es_activo = nombre == self.cronograma_actual
            color_pestaña = colores_dict.get(nombre, "#89B4FA")
            txt_color = "#11111B"

            f_p = ctk.CTkFrame(
                self.contenedor_pestanas,
                fg_color=color_pestaña,
                corner_radius=6,
                border_width=0,
            )
            f_p.pack(side="left", padx=3)

            btn = ctk.CTkButton(
                f_p,
                text=nombre,
                fg_color="transparent",
                text_color=txt_color,
                hover_color="#B4BEFE",
                font=("Segoe UI", 11, "bold" if es_activo else "normal"),
                height=28,
                border_width=0,
                command=lambda n=nombre: self.on_cambiar_cb(n),
            )
            btn.pack(side="left", padx=(4, 0))

            if self.on_editar_cb:
                btn_edit = ctk.CTkButton(
                    f_p,
                    text="✏",
                    width=22,
                    height=28,
                    fg_color="transparent",
                    hover_color="#94E2D5",
                    text_color=txt_color,
                    border_width=0,
                    command=lambda n=nombre: self.on_editar_cb(n),
                )
                btn_edit.pack(side="left", padx=0)

            if len(self.lista_cronogramas) > 1:
                btn_del = ctk.CTkButton(
                    f_p,
                    text="✕",
                    width=20,
                    height=28,
                    fg_color="transparent",
                    hover_color="#F38BA8",
                    text_color=txt_color,
                    border_width=0,
                    command=lambda n=nombre: self.on_eliminar_cb(n),
                )
                btn_del.pack(side="left", padx=(0, 4))


class GestorCalendariosGuardados:
    """Lista desplegable en acordeón para mostrar calendarios guardados que están cerrados."""

    def __init__(
        self,
        parent: ctk.CTk,
        obtener_lista_cb: Callable[[], List[str]],
        obtener_activo_cb: Callable[[], str],
        al_abrir_cronograma_cb: Callable[[str], None],
        al_borrar_cronograma_cb: Callable[[str], None],
    ):
        self.parent = parent
        self.obtener_lista_cb = obtener_lista_cb
        self.obtener_activo_cb = obtener_activo_cb
        self.al_abrir_cronograma_cb = al_abrir_cronograma_cb
        self.al_borrar_cronograma_cb = al_borrar_cronograma_cb

        self.expandido: bool = False
        self.idx_seleccionado: int = 0
        self.items_guardados: List[str] = []
        self.widgets_items: List[ctk.CTkFrame] = []

        self.frame_main = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.frame_main.pack(fill="x", padx=15, pady=(0, 5))

        self.btn_toggle = ctk.CTkButton(
            self.frame_main,
            text="Calendarios guardados >",
            anchor="w",
            fg_color="transparent",
            hover_color=("#E5E7EB", "#2A2B3C"),
            text_color=("#4B5563", "#A6ADC8"),
            font=("Segoe UI", 11, "bold"),
            command=self.toggle_desplegable,
        )
        self.btn_toggle.pack(fill="x")

        self.frame_contenido = ctk.CTkFrame(
            self.frame_main, fg_color=("#E5E7EB", "#1E1E2E"), corner_radius=8
        )

    def toggle_desplegable(self):
        self.expandido = not self.expandido
        if self.expandido:
            self.btn_toggle.configure(text="Calendarios guardados v")
            self.frame_contenido.pack(fill="x", expand=True, pady=(5, 0), padx=5)
            self.idx_seleccionado = 0
            self.actualizar_lista()
            self._activar_bindings_teclado()
        else:
            self.btn_toggle.configure(text="Calendarios guardados >")
            self.frame_contenido.pack_forget()
            self._desactivar_bindings_teclado()
            self.widgets_items.clear()
            self.items_guardados = []
            if hasattr(self.parent, "focus_set"):
                self.parent.focus_set()

    def actualizar_lista(self):
        for child in self.frame_contenido.winfo_children():
            child.destroy()

        self.widgets_items.clear()
        todos = self.obtener_lista_cb()
        pestanas_visibles = getattr(self.parent, "pestanas_abiertas", [])
        self.items_guardados = [c for c in todos if c not in pestanas_visibles]

        if not self.items_guardados:
            lbl_vacio = ctk.CTkLabel(
                self.frame_contenido,
                text="No hay otros calendarios guardados.",
                text_color=("#6B7280", "#A6ADC8"),
                font=("Segoe UI", 11, "italic"),
            )
            lbl_vacio.pack(padx=10, pady=8, anchor="w")
            return

        if self.idx_seleccionado >= len(self.items_guardados):
            self.idx_seleccionado = max(0, len(self.items_guardados) - 1)

        for i, nombre_cronograma in enumerate(self.items_guardados):
            item_frame = ctk.CTkFrame(self.frame_contenido, fg_color="transparent", corner_radius=4)
            item_frame.pack(fill="x", padx=5, pady=2)
            self.widgets_items.append(item_frame)

            lbl_nombre = ctk.CTkLabel(
                item_frame,
                text=f"📅  {nombre_cronograma}",
                text_color=("#1F2937", "#CDD6F4"),
                font=("Segoe UI", 11),
            )
            lbl_nombre.pack(side="left", padx=5)

            btn_eliminar = ctk.CTkButton(
                item_frame,
                text="🗑 Borrar (E)",
                width=80,
                height=24,
                fg_color="#F38BA8",
                text_color="#11111B",
                hover_color="#E78284",
                font=("Segoe UI", 10, "bold"),
                command=lambda n=nombre_cronograma: self._ejecutar_borrar(n),
            )
            btn_eliminar.pack(side="right", padx=(5, 5))

            btn_abrir = ctk.CTkButton(
                item_frame,
                text="Abrir (A)",
                width=70,
                height=24,
                fg_color="#89B4FA",
                text_color="#11111B",
                hover_color="#B4BEFE",
                font=("Segoe UI", 10, "bold"),
                command=lambda n=nombre_cronograma: self._ejecutar_abrir(n),
            )
            btn_abrir.pack(side="right")

        self._actualizar_resaltado()

    def _activar_bindings_teclado(self):
        """Asigna los eventos del acordeón y bloquea temporalmente los de la grilla."""
        self.parent.bind("<Up>", lambda e: self._mover_seleccion(-1))
        self.parent.bind("<Down>", lambda e: self._mover_seleccion(1))
        self.parent.bind("<a>", lambda e: self._abrir_seleccionado())
        self.parent.bind("<A>", lambda e: self._abrir_seleccionado())
        self.parent.bind("<e>", lambda e: self._borrar_seleccionado())
        self.parent.bind("<E>", lambda e: self._borrar_seleccionado())
        self.parent.bind("<Escape>", lambda e: self.toggle_desplegable())

    def _desactivar_bindings_teclado(self):
        """Desvincula totalmente las teclas del acordeón y restaura la grilla."""
        self.parent.unbind("<a>")
        self.parent.unbind("<A>")
        self.parent.unbind("<e>")
        self.parent.unbind("<E>")
        if hasattr(self.parent, "navegador_teclado") and hasattr(self.parent.navegador_teclado, "registrar_atajos"):
            self.parent.navegador_teclado.registrar_atajos()

    def _mover_seleccion(self, delta: int) -> str:
        if not self.expandido or not self.items_guardados:
            return "break"
        self.idx_seleccionado = (self.idx_seleccionado + delta) % len(self.items_guardados)
        self._actualizar_resaltado()
        return "break"

    def _actualizar_resaltado(self):
        if not self.expandido:
            return
        for i, frame in enumerate(self.widgets_items):
            if i == self.idx_seleccionado:
                frame.configure(fg_color=("#D1D5DB", "#313244"))
            else:
                frame.configure(fg_color="transparent")

    def _abrir_seleccionado(self) -> str:
        if not self.expandido:
            return ""
        if self.items_guardados and 0 <= self.idx_seleccionado < len(self.items_guardados):
            nombre = self.items_guardados[self.idx_seleccionado]
            self._ejecutar_abrir(nombre)
        return "break"

    def _borrar_seleccionado(self) -> str:
        if not self.expandido:
            return ""
        if self.items_guardados and 0 <= self.idx_seleccionado < len(self.items_guardados):
            nombre = self.items_guardados[self.idx_seleccionado]
            self._ejecutar_borrar(nombre)
        return "break"

    def _ejecutar_abrir(self, nombre: str):
        self.al_abrir_cronograma_cb(nombre)
        if self.expandido:
            self.toggle_desplegable()

    def _ejecutar_borrar(self, nombre: str):
        self.al_borrar_cronograma_cb(nombre)
        self.actualizar_lista()