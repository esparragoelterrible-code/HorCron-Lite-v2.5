import os
import sys
import json
import customtkinter as tk

CARPETA_RAIZ = os.path.dirname(os.path.abspath(__file__))
if CARPETA_RAIZ not in sys.path:
    sys.path.insert(0, CARPETA_RAIZ)

from config import (
    CATEGORIAS,
    COLOR_VARIOS,
    DIAS_ESPANOL,
    RUTA_JSON,
    cargar_configuracion,
    guardar_configuracion,
)
from exporter import exportar_a_ics, exportar_a_pdf
from features import (
    EditarHorarioModal,
    GestorHorariosGuardados,
    GestorInspectorNotas,
    GestorPestanasPuras,
)
from grid_manager import GrillaCronograma
from keyboard_navigation import NavegadorTeclado
from notificator import verificar_horario
from persistence import (
    cargar_datos_cronograma,
    cargar_json_completo,
    guardar_cronograma_y_notas,
)
from tray import ocultar_a_bandeja

# Configuración inicial de constantes visuales
COLOR_TAREA_DEFECTO = ("#BB7641", "#F59E0B")
COLOR_VACIO_FONDO = "#2A2B3C"
COLOR_VACIO_BORDE = "#45475A"


class CronogramaApp(tk.CTk):
    def __init__(self):
        super().__init__()

        # 1. Carga de Configuración en Memoria
        self.config = cargar_configuracion()
        tk.set_appearance_mode(self.config.get("tema", "Dark").lower())

        self.cronograma_actual = self.config.get("cronograma_activo", "Principal")
        self.lista_cronogramas = self.config.get("cronogramas_lista", ["Principal"])
        self.pestanas_abiertas = self.config.get("pestanas_abiertas", list(self.lista_cronogramas))

        # Referencias activas para ventanas modales
        self.v_exportar_ref = None
        self.v_crear_ref = None

        # 2. Configuración de la Ventana Principal
        self.title("HorCron Lite v2.5 🗓")
        self.geometry("1050x650")
        self.minsize(850, 500)
        self.configure(fg_color=("#F3F4F6", "#181825"))

        # Métodos para integración con módulos externos
        self.actualizar_tema = self.reaplicar_colores_grilla
        self.actualizar_formato_hora = self.actualizar_formato_hora_grilla
        self.protocol("WM_DELETE_WINDOW", lambda: ocultar_a_bandeja(self))

        # 3. Inicialización de Componentes de la Interfaz
        self._inicializar_pestanas()
        self._inicializar_barra_inferior()
        self._inicializar_inspector_y_grilla()

        # 4. Vinculación de Atajos y Navegación por Teclado
        self.navegador_teclado = NavegadorTeclado(self)
        self.navegador_teclado.registrar_atajos()

        # 5. Carga Inicial y Programación de Notificaciones
        self.renderizar_y_cargar()
        self._programar_verificacion_notificaciones()

    # ==========================================
    # INICIALIZACIÓN DE WIDGETS
    # ==========================================

    def _inicializar_pestanas(self):
        self.gestor_pestanas = GestorPestanasPuras(
            self,
            self.pestanas_abiertas,
            self.cronograma_actual,
            self.cb_cambiar_cronograma,
            self.cb_crear_cronograma,
            self.cb_cerrar_pestana,
            self.cb_renombrar_cronograma,
        )

    def _inicializar_barra_inferior(self):
        self.frame_inferior = tk.CTkFrame(self, fg_color="transparent")
        self.frame_inferior.pack(side="bottom", fill="x", padx=15, pady=(2, 8))

        self.btn_guardar = tk.CTkButton(
            self.frame_inferior,
            text="💾 Guardar (Enter)",
            command=self.guardar_datos,
            fg_color="#89B4FA",
            text_color="#11111B",
            hover_color="#B4BEFE",
            font=("Segoe UI", 12, "bold"),
        )
        self.btn_guardar.pack(side="left", padx=(0, 5))

        self.btn_config = tk.CTkButton(
            self.frame_inferior,
            text="⚙ Configurar (Ctrl+O)",
            width=130,
            command=self.abrir_configuracion,
            fg_color=("#D1D5DB", "#45475A"),
            text_color=("#1F2937", "#CDD6F4"),
            hover_color=("#9CA3AF", "#585B70"),
        )
        self.btn_config.pack(side="left", padx=5)

        self.btn_exportar = tk.CTkButton(
            self.frame_inferior,
            text="📤 Exportar (Ctrl+M)",
            width=130,
            command=self.abrir_menu_exportar,
            fg_color=("#D1D5DB", "#45475A"),
            text_color=("#1F2937", "#CDD6F4"),
            hover_color=("#9CA3AF", "#585B70"),
        )
        self.btn_exportar.pack(side="left", padx=5)

        self.btn_atajos = tk.CTkButton(
            self.frame_inferior,
            text="⌨ Atajos (Ctrl+H)",
            width=120,
            command=lambda: self.navegador_teclado._abrir_ayuda_atajos(),
            fg_color=("#D1D5DB", "#45475A"),
            text_color=("#1F2937", "#CDD6F4"),
            hover_color=("#9CA3AF", "#585B70"),
            font=("Segoe UI", 12),
        )
        self.btn_atajos.pack(side="left", padx=5)

        self.lbl_estado = tk.CTkLabel(
            self.frame_inferior, text="", font=("Segoe UI", 12, "bold"), text_color="#3FB950"
        )
        self.lbl_estado.pack(side="right", padx=10)

        self.gestor_guardados = GestorHorariosGuardados(
            self,
            obtener_lista_cb=lambda: self.lista_cronogramas,
            obtener_activo_cb=lambda: self.cronograma_actual,
            al_abrir_cronograma_cb=self.cb_abrir_cronograma_guardado,
            al_borrar_cronograma_cb=self.cb_eliminar_definitivamente,
        )

    def _inicializar_inspector_y_grilla(self):
        horas_rango = [f"{h:02d}:00" for h in range(6, 23)]

        self.gestor_notas = GestorInspectorNotas(
            self,
            lambda: self.cronograma_actual,
            lambda: RUTA_JSON,
            self.formatear_hora_texto,
        )
        self.gestor_notas.frame_container.pack_forget()
        self.gestor_notas.frame_container.pack(side="bottom", fill="x", padx=10, pady=(2, 5))

        self.grilla = GrillaCronograma(
            self,
            DIAS_ESPANOL,
            horas_rango,
            self.config.get("formato_hora", "24h"),
            self.formatear_hora_texto,
            self.al_seleccionar_celda,
            self.guardar_datos,
        )

    # ==========================================
    # LÓGICA DE NEGOCIO Y COLORES
    # ==========================================

    def obtener_color_por_categoria(self, texto: str):
        if not texto:
            return (COLOR_VACIO_FONDO, COLOR_VACIO_BORDE)

        texto_lower = texto.lower().strip()
        cat_guardadas = self.config.get("categorias", {})

        # 1. Categorías personalizadas del usuario
        for palabra_clave, data_color in cat_guardadas.items():
            p_clean = palabra_clave.lower().strip()
            if p_clean and (p_clean in texto_lower or texto_lower in p_clean):
                if isinstance(data_color, dict):
                    return data_color.get("fondo", "#1E3A5F"), data_color.get("borde", "#3B82F6")
                elif isinstance(data_color, (list, tuple)):
                    return data_color[0], data_color[1]
                return data_color, data_color

        # 2. Categorías predeterminadas
        for cat_data in CATEGORIAS.values():
            for p in cat_data.get("palabras", []):
                if p.lower() in texto_lower:
                    col = cat_data.get("colores", COLOR_VARIOS)
                    return col if isinstance(col, (list, tuple)) else (col, col)

        # 3. Descarte: Tareas no clasificadas -> Naranja por defecto
        return COLOR_TAREA_DEFECTO

    def reaplicar_colores_grilla(self):
        if not hasattr(self, "grilla") or not hasattr(self.grilla, "entradas"):
            return

        for (dia, hora), casilla in self.grilla.entradas.items():
            texto = casilla.get().strip()
            if not texto:
                color_fondo, color_borde, color_texto = COLOR_VACIO_FONDO, COLOR_VACIO_BORDE, "#CDD6F4"
            else:
                color_fondo, color_borde = self.obtener_color_por_categoria(texto)
                color_texto = "#FFFFFF"

            casilla.configure(
                fg_color=color_fondo,
                border_color=color_borde,
                text_color=color_texto,
                placeholder_text_color="#A6ADC8",
            )

    @staticmethod
    def formatear_hora_texto(hora_24h: str, formato: str) -> str:
        if formato == "12h":
            h = int(hora_24h.split(":")[0])
            periodo = "AM" if h < 12 else "PM"
            h_12 = h % 12 or 12
            return f"{h_12:02d}:00 {periodo}"
        return hora_24h

    def actualizar_formato_hora_grilla(self):
        self.config = cargar_configuracion()
        fmt = self.config.get("formato_hora", "24h")
        self.grilla.actualizar_formato_hora(fmt)

    def mostrar_mensaje_estado(self, texto: str, color: str):
        self.lbl_estado.configure(text=texto, text_color=color)
        self.after(3000, lambda: self.lbl_estado.configure(text=""))

    # ==========================================
    # GESTIÓN DE DATOS Y ESTADOS
    # ==========================================

    def guardar_datos(self):
        try:
            guardar_cronograma_y_notas(
                RUTA_JSON, self.cronograma_actual, self.grilla.entradas, self.gestor_notas
            )
            self.reaplicar_colores_grilla()
            self.mostrar_mensaje_estado("✔ Cambios guardados", "#3FB950")
        except Exception as e:
            self.mostrar_mensaje_estado("✖ Error al guardar", "#F85149")
            print(f"[Error Guardado]: {e}")

    def cargar_datos(self):
        cargar_datos_cronograma(RUTA_JSON, self.cronograma_actual, self.grilla.entradas)
        self.reaplicar_colores_grilla()

    def renderizar_y_cargar(self):
        """Carga y renderiza el cronograma activo en un único ciclo sincrónico."""
        self.gestor_pestanas.renderizar(self.pestanas_abiertas, self.cronograma_actual)
        self.cargar_datos()
        
        # Actualizar placeholders explícitamente al iniciar o cambiar de pestaña
        if hasattr(self, "grilla"):
            self.grilla.actualizar_placeholders()

        if hasattr(self, "navegador_teclado"):
            self.navegador_teclado.construir_matriz()

    def sincronizar_configuracion(self):
        self.config["cronogramas_lista"] = self.lista_cronogramas
        self.config["pestanas_abiertas"] = self.pestanas_abiertas
        self.config["cronograma_activo"] = self.cronograma_actual
        guardar_configuracion(self.config)

    # ==========================================
    # CALLBACKS DE INTERACCIÓN
    # ==========================================

    def al_seleccionar_celda(self, dia, hora):
        casilla = self.grilla.entradas[(dia, hora)]
        texto_tarea = casilla.get().strip()
        self.gestor_notas.cargar_nota_celda(
            dia, hora, texto_tarea, self.config.get("formato_hora", "24h")
        )

    def cb_cambiar_cronograma(self, nuevo_nombre):
        if nuevo_nombre != self.cronograma_actual:
            self.guardar_datos()
            self.cronograma_actual = nuevo_nombre
            self.sincronizar_configuracion()
            self.renderizar_y_cargar()

    def cb_crear_cronograma(self):
        if hasattr(self, "v_crear_ref") and self.v_crear_ref is not None and self.v_crear_ref.winfo_exists():
            self.v_crear_ref.destroy()
            self.v_crear_ref = None
            self.focus_set()
            return

        top = tk.CTkToplevel(self)
        self.v_crear_ref = top
        top.title("Nuevo Cronograma")
        top.geometry("340x160")
        top.resizable(False, False)
        top.attributes("-topmost", True)
        top.grab_set()
        top.focus_force()

        lbl = tk.CTkLabel(
            top, text="Nombre del nuevo cronograma:", font=("Segoe UI", 12, "bold")
        )
        lbl.pack(pady=(15, 8))

        entry_nombre = tk.CTkEntry(top, width=260, font=("Segoe UI", 11))
        entry_nombre.pack(pady=5)
        entry_nombre.focus_set()

        def _cerrar_dialogo():
            if self.v_crear_ref and self.v_crear_ref.winfo_exists():
                self.v_crear_ref.destroy()
            self.v_crear_ref = None
            self.focus_set()

        def _confirmar():
            nombre = entry_nombre.get().strip()
            _cerrar_dialogo()
            if nombre:
                self.guardar_datos()
                if nombre not in self.lista_cronogramas:
                    self.lista_cronogramas.append(nombre)
                if nombre not in self.pestanas_abiertas:
                    self.pestanas_abiertas.append(nombre)

                self.cronograma_actual = nombre
                self.sincronizar_configuracion()
                self.renderizar_y_cargar()
                self.gestor_guardados.actualizar_lista()

        frame_btns = tk.CTkFrame(top, fg_color="transparent")
        frame_btns.pack(pady=12)

        btn_ok = tk.CTkButton(
            frame_btns,
            text="Ok",
            width=110,
            command=_confirmar,
            fg_color="#3B82F6",
            hover_color="#1D4ED8",
            font=("Segoe UI", 11, "bold"),
        )
        btn_ok.pack(side="left", padx=5)

        btn_cancel = tk.CTkButton(
            frame_btns,
            text="Cancelar (Esc)",
            width=110,
            command=_cerrar_dialogo,
            fg_color="#45475A",
            hover_color="#585B70",
            font=("Segoe UI", 11),
        )
        btn_cancel.pack(side="left", padx=5)

        entry_nombre.bind("<Return>", lambda e: _confirmar())
        top.bind("<Escape>", lambda e: _cerrar_dialogo())
        top.bind("<F1>", lambda e: _cerrar_dialogo())
        top.bind("<Control-t>", lambda e: _cerrar_dialogo())
        top.bind("<Control-T>", lambda e: _cerrar_dialogo())

    def cb_cerrar_pestana(self, nombre):
        if nombre in self.pestanas_abiertas:
            self.pestanas_abiertas.remove(nombre)

            if self.cronograma_actual == nombre:
                if self.pestanas_abiertas:
                    self.cronograma_actual = self.pestanas_abiertas[0]
                elif self.lista_cronogramas:
                    self.cronograma_actual = self.lista_cronogramas[0]

            self.sincronizar_configuracion()
            self.renderizar_y_cargar()
            self.gestor_guardados.actualizar_lista()

    def cb_abrir_cronograma_guardado(self, nombre_cronograma):
        self.guardar_datos()
        if nombre_cronograma not in self.pestanas_abiertas:
            self.pestanas_abiertas.append(nombre_cronograma)

        self.cronograma_actual = nombre_cronograma
        self.sincronizar_configuracion()
        self.renderizar_y_cargar()
        self.gestor_guardados.actualizar_lista()

    def cb_renombrar_cronograma(self, nombre_viejo):
        def guardar_cambios(nuevo_nombre, nuevo_color):
            if not nuevo_nombre:
                return

            self.guardar_datos()

            if nombre_viejo in self.lista_cronogramas:
                idx = self.lista_cronogramas.index(nombre_viejo)
                self.lista_cronogramas[idx] = nuevo_nombre

            if nombre_viejo in self.pestanas_abiertas:
                idx = self.pestanas_abiertas.index(nombre_viejo)
                self.pestanas_abiertas[idx] = nuevo_nombre

            if self.cronograma_actual == nombre_viejo:
                self.cronograma_actual = nuevo_nombre

            # Carga vía caché de persistencia
            datos = cargar_json_completo(RUTA_JSON)
            if nombre_viejo in datos:
                datos[nuevo_nombre] = datos.pop(nombre_viejo)
            if "_notas" in datos and nombre_viejo in datos["_notas"]:
                datos["_notas"][nuevo_nombre] = datos["_notas"].pop(nombre_viejo)

            with open(RUTA_JSON, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=4)

            colores = self.config.get("colores_pestanas", {})
            colores[nuevo_nombre] = nuevo_color
            if nombre_viejo in colores and nombre_viejo != nuevo_nombre:
                del colores[nombre_viejo]
            self.config["colores_pestanas"] = colores

            self.sincronizar_configuracion()
            self.renderizar_y_cargar()
            self.gestor_guardados.actualizar_lista()

        color_actual = self.config.get("colores_pestanas", {}).get(nombre_viejo, "#89B4FA")
        EditarHorarioModal(
            parent=self,
            nombre_actual=nombre_viejo,
            color_actual=color_actual,
            callback_guardar=guardar_cambios,
        )

    def cb_eliminar_definitivamente(self, nombre_cronograma):
        if len(self.lista_cronogramas) <= 1:
            self.mostrar_mensaje_estado("⚠ Se requiere al menos 1 cronograma", "#E69138")
            return

        if nombre_cronograma in self.lista_cronogramas:
            self.lista_cronogramas.remove(nombre_cronograma)

        if nombre_cronograma in self.pestanas_abiertas:
            self.pestanas_abiertas.remove(nombre_cronograma)

        self.sincronizar_configuracion()
        self.gestor_pestanas.renderizar(self.pestanas_abiertas, self.cronograma_actual)
        self.gestor_guardados.actualizar_lista()
        self.mostrar_mensaje_estado("🗑 Cronograma eliminado", "#F38BA8")

    # ==========================================
    # MODALES Y HERRAMIENTAS EXTERNAS
    # ==========================================

    def abrir_configuracion(self):
        """Abre u oculta el panel de configuración permitiendo el toggle por teclado/botón."""
        if hasattr(self, "navegador_teclado") and self.navegador_teclado:
            self.navegador_teclado._abrir_config()
        else:
            try:
                from config_window import VentanaConfiguracion
                v_config = VentanaConfiguracion(self)
                self.wait_window(v_config)
                self.actualizar_formato_hora_grilla()
                self.reaplicar_colores_grilla()
            except ImportError:
                self.mostrar_mensaje_estado("⚠ Módulo de configuración desactivado", "#E69138")

    def abrir_menu_exportar(self):
        if self.v_exportar_ref is not None and self.v_exportar_ref.winfo_exists():
            self.v_exportar_ref.destroy()
            self.v_exportar_ref = None
            self.focus_set()
            return

        datos_completos = cargar_json_completo(RUTA_JSON)
        datos_actuales = datos_completos.get(self.cronograma_actual, {})

        if not datos_actuales:
            self.mostrar_mensaje_estado("⚠ No hay datos para exportar", "#E69138")
            return

        top_exp = tk.CTkToplevel(self)
        self.v_exportar_ref = top_exp
        top_exp.title("Exportar Cronograma 📄")
        top_exp.geometry("340x200")
        top_exp.resizable(False, False)
        top_exp.attributes("-topmost", True)
        top_exp.grab_set()
        top_exp.focus_force()

        lbl = tk.CTkLabel(
            top_exp, text="Selecciona el formato de exportación:", font=("Segoe UI", 12, "bold")
        )
        lbl.pack(pady=(15, 10))

        def _cerrar_top_exp():
            if self.v_exportar_ref and self.v_exportar_ref.winfo_exists():
                self.v_exportar_ref.destroy()
            self.v_exportar_ref = None
            self.focus_set()

        def exp_pdf():
            _cerrar_top_exp()
            self._exportar_directo_pdf()

        def exp_ics():
            _cerrar_top_exp()
            self._exportar_directo_ics()

        btn_pdf = tk.CTkButton(
            top_exp, text="📄 Exportar a Documento PDF (Ctrl+P)", command=exp_pdf, fg_color="#3B82F6", hover_color="#1D4ED8"
        )
        btn_pdf.pack(fill="x", padx=20, pady=6)

        btn_ics = tk.CTkButton(
            top_exp, text="📅 Exportar a iCalendar .ics (Ctrl+E)", command=exp_ics, fg_color="#2D702B", hover_color="#2A693D"
        )
        btn_ics.pack(fill="x", padx=20, pady=6)

        top_exp.bind("<Control-p>", lambda e: exp_pdf())
        top_exp.bind("<Control-P>", lambda e: exp_pdf())
        top_exp.bind("<Control-e>", lambda e: exp_ics())
        top_exp.bind("<Control-E>", lambda e: exp_ics())
        top_exp.bind("<Control-m>", lambda e: _cerrar_top_exp())
        top_exp.bind("<Control-M>", lambda e: _cerrar_top_exp())
        top_exp.bind("<Escape>", lambda e: _cerrar_top_exp())

    def _exportar_directo_pdf(self):
        datos_completos = cargar_json_completo(RUTA_JSON)
        datos_actuales = datos_completos.get(self.cronograma_actual, {})
        if not datos_actuales:
            self.mostrar_mensaje_estado("⚠ No hay datos para exportar", "#E69138")
            return
        if exportar_a_pdf(datos_actuales, self.cronograma_actual, RUTA_JSON):
            self.mostrar_mensaje_estado("✔ Exportado a PDF con éxito", "#3FB950")

    def _exportar_directo_ics(self):
        datos_completos = cargar_json_completo(RUTA_JSON)
        datos_actuales = datos_completos.get(self.cronograma_actual, {})
        if not datos_actuales:
            self.mostrar_mensaje_estado("⚠ No hay datos para exportar", "#E69138")
            return
        if exportar_a_ics(datos_actuales, self.cronograma_actual):
            self.mostrar_mensaje_estado("✔ Exportado a .ICS con éxito", "#3FB950")

    # ==========================================
    # NOTIFICACIONES EN BUCLE SEGURO (AFTER)
    # ==========================================

    def _programar_verificacion_notificaciones(self):
        try:
            verificar_horario()
        except Exception as e:
            print(f"[Error Notificación]: {e}")
        self.after(60000, self._programar_verificacion_notificaciones)


if __name__ == "__main__":
    app = CronogramaApp()
    app.mainloop()