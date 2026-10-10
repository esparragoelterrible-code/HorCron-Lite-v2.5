import customtkinter as tk

class GestorToolTipGlobal:
    """Gestor singleton que maneja UNA sola ventana de tooltip para toda la aplicación. Elimina por completo el bug de ventanas huérfanas o congeladas en pantalla."""
    _instancia_ventana = None
    _label = None
    _timer_delay = None
    _timer_autoclose = None
    _widget_actual = None

    @classmethod
    def _inicializar_ventana(cls, root):
        if cls._instancia_ventana is None or not cls._instancia_ventana.winfo_exists():
            cls._instancia_ventana = tk.CTkToplevel(root)
            cls._instancia_ventana.wm_overrideredirect(True)
            cls._instancia_ventana.attributes("-topmost", True)
            cls._instancia_ventana.withdraw()  # Nace oculta

            cls._label = tk.CTkLabel(
                cls._instancia_ventana,
                text="",
                font=("Segoe UI", 11, "bold"),
                fg_color=("#E5E7EB", "#1E1E2E"),
                text_color=("#111827", "#CDD6F4"),
                corner_radius=6,
                padx=8,
                pady=4
            )
            cls._label.pack()

    @classmethod
    def solicitar_mostrar(cls, widget, texto: str, delay_ms: int = 300):
        cls.ocultar()  # Limpia cualquier estado previo inmediatamente

        if len(texto) <= 12 or not texto:
            return

        cls._widget_actual = widget
        # Espera un tiempo mínimo antes de mostrar para filtrar movimientos rápidos del mouse (debounce)
        cls._timer_delay = widget.after(delay_ms, lambda: cls._desplegar(widget, texto))

    @classmethod
    def _desplegar(cls, widget, texto: str):
        if cls._widget_actual != widget:
            return

        cls._inicializar_ventana(widget)
        cls._label.configure(text=texto)
        cls._instancia_ventana.update_idletasks()

        # Calcular posición
        try:
            ancho_tooltip = cls._instancia_ventana.winfo_width()
            alto_tooltip = cls._instancia_ventana.winfo_height()

            # Posiciona el tooltip a la IZQUIERDA del botón y alineado verticalmente
            x = widget.winfo_rootx() - ancho_tooltip - 8
            y = widget.winfo_rooty() - (alto_tooltip // 2) + (widget.winfo_height() // 2)

            # Control de bordes para evitar que se salga de pantalla
            if x < 10:
                x = widget.winfo_rootx() + widget.winfo_width() + 8
            if y < 10:
                y = 10

            cls._instancia_ventana.wm_geometry(f"+{x}+{y}")
            cls._instancia_ventana.deiconify()
            cls._instancia_ventana.lift()
        except Exception:
            cls.ocultar()
            return

        # Auto-ocultar tras 3.5 segundos
        cls._timer_autoclose = widget.after(3500, cls.ocultar)

    @classmethod
    def ocultar(cls, event=None):
        if cls._timer_delay and cls._widget_actual:
            try:
                cls._widget_actual.after_cancel(cls._timer_delay)
            except Exception:
                pass
            cls._timer_delay = None

        if cls._timer_autoclose and cls._widget_actual:
            try:
                cls._widget_actual.after_cancel(cls._timer_autoclose)
            except Exception:
                pass
            cls._timer_autoclose = None

        cls._widget_actual = None

        # Ocultar la ventana de la pantalla en lugar de destruirla
        if cls._instancia_ventana and cls._instancia_ventana.winfo_exists():
            cls._instancia_ventana.withdraw()


class ToolTipDinamico:
    """Para celdas de la grilla que contienen texto largo."""
    def __init__(self, widget):
        self.widget = widget
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
        self.widget.bind("<ButtonPress>", self._on_leave)
        self.widget.bind("<FocusOut>", self._on_leave)

    def _on_enter(self, event=None):
        texto = self.widget.get().strip()
        GestorToolTipGlobal.solicitar_mostrar(self.widget, texto)

    def _on_leave(self, event=None):
        GestorToolTipGlobal.ocultar()