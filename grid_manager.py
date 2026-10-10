import customtkinter as tk  # type: ignore
from typing import Dict, List, Tuple, Callable, Any
from config import cargar_configuracion
from tooltips import ToolTipDinamico

class GrillaCronograma:
    """Maneja la grilla principal de celdas para el cronograma de actividades."""

    def __init__(
        self,
        parent: tk.CTk,
        dias: List[str],
        horas: List[str],
        formato_actual: str,
        formatear_hora_fn: Callable[[str, str], str],
        al_seleccionar_celda_cb: Callable[[str, str], None],
        al_guardar_cb: Callable[[], None],
    ) -> None:
        self.parent = parent
        self.dias = dias
        self.horas = horas
        self.formato_actual = formato_actual
        self.formatear_hora_fn = formatear_hora_fn
        self.al_seleccionar_celda_cb = al_seleccionar_celda_cb
        self.al_guardar_cb = al_guardar_cb

        self.entradas: Dict[Tuple[str, str], tk.CTkEntry] = {}
        self.etiquetas_horas: Dict[str, tk.CTkLabel] = {}
        self.scroll_frame: Any = None

        self._construir_ui()

    def _obtener_texto_placeholder(self) -> str:
        cfg = cargar_configuracion()
        mostrar_vacio = cfg.get("mostrar_indicador_vacio", True)
        return "vacío..." if mostrar_vacio else ""

    def _construir_ui(self) -> None:
        self.scroll_frame = tk.CTkScrollableFrame(
            self.parent, fg_color=("#E5E7EB", "#1E1E2E"), corner_radius=10
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.scroll_frame.grid_columnconfigure(0, weight=0)
        for col_idx in range(1, len(self.dias) + 1):
            self.scroll_frame.grid_columnconfigure(col_idx, weight=1)

        lbl_horas = tk.CTkLabel(
            self.scroll_frame,
            text="Horas",
            font=("Segoe UI", 12, "bold"),
            text_color=("#4B5563", "#A6ADC8"),
        )
        lbl_horas.grid(row=0, column=0, padx=10, pady=5)

        for col_idx, dia in enumerate(self.dias, start=1):
            lbl_dia = tk.CTkLabel(
                self.scroll_frame,
                text=dia,
                text_color=("#1D4ED8", "#7AA2F7"),
                font=("Segoe UI", 13, "bold"),
            )
            lbl_dia.grid(row=0, column=col_idx, padx=8, pady=10)

        txt_placeholder = self._obtener_texto_placeholder()

        for row_idx, hora in enumerate(self.horas, start=1):
            texto_hora_fmt = self.formatear_hora_fn(hora, self.formato_actual)
            texto_hora = tk.CTkLabel(
                self.scroll_frame,
                text=texto_hora_fmt,
                text_color=("#4B5563", "#A6ADC8"),
                font=("Segoe UI", 11, "bold"),
            )
            texto_hora.grid(row=row_idx, column=0, padx=8, pady=4)
            self.etiquetas_horas[hora] = texto_hora

            for col_idx, dia in enumerate(self.dias, start=1):
                casilla = tk.CTkEntry(
                    self.scroll_frame,
                    placeholder_text=txt_placeholder,
                    height=32,
                    corner_radius=6,
                    border_width=1,
                    fg_color="#2A2B3C",
                    border_color="#45475A",
                    text_color="#CDD6F4",
                    placeholder_text_color="#A6ADC8",
                )
                casilla.grid(row=row_idx, column=col_idx, padx=3, pady=3, sticky="ew")

                ToolTipDinamico(casilla)
                casilla.bind("<Return>", lambda e: self.al_guardar_cb())
                casilla.bind(
                    "<FocusIn>",
                    lambda e, d=dia, h=hora: self.al_seleccionar_celda_cb(d, h),
                )

                self.entradas[(dia, hora)] = casilla

    def cargar_datos(self, datos_cronograma: Dict[Tuple[str, str], str]) -> None:
        """Carga datos directamente reutilizando la matriz visual de celdas sin re-crear la UI."""
        self.limpiar()
        for (dia, hora), texto in datos_cronograma.items():
            if (dia, hora) in self.entradas and texto:
                self.entradas[(dia, hora)].insert(0, texto)

    def limpiar(self) -> None:
        """Limpia el texto de todas las casillas de forma directa."""
        for casilla in self.entradas.values():
            casilla.delete(0, tk.END)

    def actualizar_placeholders(self) -> None:
        """Actualiza la propiedad placeholder_text directamente sin recrear la grilla."""
        txt_ph = self._obtener_texto_placeholder()
        for casilla in self.entradas.values():
            casilla.configure(placeholder_text=txt_ph)

    def actualizar_placeholders_con_valor(self, mostrar_vacio: bool) -> None:
        """Actualiza los placeholders de la grilla usando un valor booleano directo (para vistas previas)."""
        txt_ph = "vacío..." if mostrar_vacio else ""
        for casilla in self.entradas.values():
            casilla.configure(placeholder_text=txt_ph)

    def actualizar_formato_hora(self, nuevo_formato: str) -> None:
        """Actualiza las etiquetas laterales de hora sin tocar las celdas."""
        self.formato_actual = nuevo_formato
        for hora_key, widget_lbl in self.etiquetas_horas.items():
            widget_lbl.configure(
                text=self.formatear_hora_fn(hora_key, self.formato_actual)
            )