import customtkinter as tk

class VentanaAtajosTeclado(tk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Atajos de Teclado ⌨")
        self.geometry("460x440")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()

        self.configure(fg_color=("#F3F4F6", "#1E1E2E"))

        lbl_titulo = tk.CTkLabel(
            self,
            text="⌨ Guía de Navegación por Teclado",
            font=("Segoe UI", 16, "bold"),
            text_color=("#111827", "#CDD6F4"),
        )
        lbl_titulo.pack(pady=(15, 10))

        self.frame_lista = tk.CTkScrollableFrame(
            self,
            fg_color=("#E5E7EB", "#181825"),
            corner_radius=8,
            width=410,
            height=310,
        )
        self.frame_lista.pack(padx=15, pady=5, fill="both", expand=True)

        atajos = [
            ("Navegación en Grilla", [
                ("Flechas (↑ ↓ ← →)", "Moverse entre celdas"),
                ("Enter", "Entrar a editar / Guardar cambios"),
                ("Escape", "Salir del modo edición"),
            ]),
            ("Pestañas y Cronogramas", [
                ("F1 / Ctrl + T", "Crear nuevo cronograma"),
                ("F2", "Desplegar calendarios guardados"),
                ("↑ / ↓ (en F2)", "Navegar guardados"),
                ("A / E (en F2)", "Abrir / Borrar guardado"),
                ("Ctrl + , / Ctrl + .", "Pestaña Anterior / Siguiente"),
            ]),
            ("Acciones Rápidas", [
                ("F11", "Pantalla Completa (Toggle)"),
                ("Ctrl + N", "Abrir / Cerrar Inspector de Notas"),
                ("Ctrl + L", "Limpiar casilla seleccionada"),
                ("Ctrl + O", "Abrir / Cerrar Ventana de Configuración"),
            ]),
            ("Exportación y Ayuda", [
                ("Ctrl + M", "Opciones de Exportación"),
                ("Ctrl + H", "Mostrar / Ocultar esta guía de atajos"),
            ]),
        ]

        for categoria, items in atajos:
            lbl_cat = tk.CTkLabel(
                self.frame_lista,
                text=categoria,
                font=("Segoe UI", 12, "bold"),
                text_color="#89B4FA",
                anchor="w",
            )
            lbl_cat.pack(fill="x", padx=10, pady=(10, 4))

            for tecla, desc in items:
                f_item = tk.CTkFrame(self.frame_lista, fg_color="transparent")
                f_item.pack(fill="x", padx=10, pady=2)

                lbl_key = tk.CTkLabel(
                    f_item,
                    text=f" {tecla} ",
                    font=("Consolas", 11, "bold"),
                    fg_color=("#D1D5DB", "#313244"),
                    text_color=("#1F2937", "#F5E0DC"),
                    corner_radius=4,
                )
                lbl_key.pack(side="left")

                lbl_desc = tk.CTkLabel(
                    f_item,
                    text=f"  {desc}",
                    font=("Segoe UI", 11),
                    text_color=("#4B5563", "#BAC2DE"),
                )
                lbl_desc.pack(side="left")

        btn_cerrar = tk.CTkButton(
            self,
            text="Entendido (Esc)",
            command=self._cerrar_modal,
            fg_color="#89B4FA",
            text_color="#11111B",
            hover_color="#B4BEFE",
            font=("Segoe UI", 12, "bold"),
        )
        btn_cerrar.pack(pady=12)

        # Controles de teclado
        self.bind("<Escape>", lambda e: self._cerrar_modal())
        self.bind("<Up>", lambda e: self._scroll_v(-1))
        self.bind("<Down>", lambda e: self._scroll_v(1))

        # Teclas directas para cerrar la modal si está en foco
        self.bind("<Control-h>", lambda e: self._cerrar_modal())
        self.bind("<Control-H>", lambda e: self._cerrar_modal())

    def _scroll_v(self, direccion):
        """Desplaza el panel verticalmente de forma segura."""
        if hasattr(self.frame_lista, "_parent_canvas"):
            self.frame_lista._parent_canvas.yview_scroll(direccion * 6, "units")

    def _cerrar_modal(self):
        """Cierra la ventana modal y devuelve el foco a la ventana principal."""
        if self.master and hasattr(self.master, "focus_set"):
            self.master.focus_set()
        self.destroy()