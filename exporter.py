# exporter_2.py
from datetime import datetime, timedelta
import os
import uuid
from tkinter import filedialog
from typing import Dict, Any

try:
    from icalendar import Calendar, Event
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Table, TableStyle
except ImportError as e:
    raise ImportError(
        f"Faltan dependencias de exportación. Ejecuta: 'pip install reportlab icalendar'. Detalles: {e}"
    )

from config import DIAS_ESPANOL
from persistence import cargar_json_completo

def _extraer_texto_actividad(valor_celda: Any) -> str:
    """Extrae el texto simple de la celda, soportando cadenas o diccionarios."""
    if isinstance(valor_celda, dict):
        return str(valor_celda.get("texto", "")).strip()
    if valor_celda is None:
        return ""
    return str(valor_celda).strip()


def exportar_a_pdf(
    datos_cronograma: Dict[str, Any],
    nombre_cronograma: str = "Principal",
    ruta_json: str = "cronograma_data.json",
) -> bool:
    """Genera un archivo PDF con el cronograma y una página secundaria opcional con notas detalladas."""
    archivo_destino = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("Archivos PDF", "*.pdf")],
        title=f"Exportar {nombre_cronograma} a PDF",
        initialfile=f"Cronograma_{nombre_cronograma}.pdf",
    )

    if not archivo_destino:
        return False

    try:
        doc = SimpleDocTemplate(
            archivo_destino,
            pagesize=landscape(A4),
            rightMargin=20,
            leftMargin=20,
            topMargin=20,
            bottomMargin=20,
        )

        elements = []
        styles = getSampleStyleSheet()

        # Estilos visuales
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Title"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#1E3A5F"),
            alignment=1,
        )

        subtitle_style = ParagraphStyle(
            "SubtitleStyle",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1E3A5F"),
            alignment=0,
        )

        cell_style = ParagraphStyle(
            "CellStyle",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            alignment=1,
        )

        cell_header_style = ParagraphStyle(
            "HeaderStyle",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
            textColor=colors.white,
            alignment=1,
        )

        nota_item_style = ParagraphStyle(
            "NotaItemStyle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#2A2B3C"),
        )

        # Página 1: Tabla principal del cronograma
        elements.append(
            Paragraph(f"<b>Cronograma: {nombre_cronograma}</b>", title_style)
        )
        elements.append(Paragraph("<br/><br/>", styles["Normal"]))

        horas = [f"{h:02d}:00" for h in range(6, 23)]
        encabezado = ["Hora"] + DIAS_ESPANOL

        data_tabla = [
            [Paragraph(f"<b>{col}</b>", cell_header_style) for col in encabezado]
        ]

        json_completo = cargar_json_completo(ruta_json)
        notas_calendario = (
            json_completo.get("_notas", {}).get(nombre_cronograma, {})
        )

        for hora in horas:
            fila = [Paragraph(f"<b>{hora}</b>", cell_style)]
            for dia in DIAS_ESPANOL:
                clave = f"{dia}_{hora}"
                texto_actividad = _extraer_texto_actividad(
                    datos_cronograma.get(clave, "")
                )

                if clave in notas_calendario and str(notas_calendario[clave]).strip():
                    texto_actividad += "*"

                texto_html = texto_actividad.replace("\n", "<br/>")
                fila.append(Paragraph(texto_html, cell_style))
            data_tabla.append(fila)

        col_widths = [50] + [95] * 7
        tabla = Table(data_tabla, colWidths=col_widths, repeatRows=1)
        tabla.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#F1F5F9")),
                (
                    "ROWBACKGROUNDS",
                    (1, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F8FAFC")],
                ),
            ])
        )
        elements.append(tabla)

        # Página 2: Anotaciones y detalles (opcional si existen notas)
        if notas_calendario:
            notas_activas = {
                k: str(v).strip()
                for k, v in notas_calendario.items()
                if v and str(v).strip()
            }

            if notas_activas:
                elements.append(PageBreak())
                elements.append(
                    Paragraph(
                        "<b>Anotaciones y Detalles de Actividades</b>",
                        subtitle_style,
                    )
                )
                elements.append(Paragraph("<br/>", styles["Normal"]))

                data_notas_tabla = [[
                    Paragraph("<b>Bloque / Horario</b>", cell_header_style),
                    Paragraph("<b>Actividad</b>", cell_header_style),
                    Paragraph("<b>Nota / Detalle</b>", cell_header_style),
                ]]

                for clave, texto_nota in notas_activas.items():
                    partes = clave.split("_")
                    dia_str = partes[0] if len(partes) > 0 else ""
                    hora_str = partes[1] if len(partes) > 1 else ""

                    actividad_asociada = _extraer_texto_actividad(
                        datos_cronograma.get(clave, "Sin actividad")
                    )
                    if not actividad_asociada:
                        actividad_asociada = "(Sin nombre)"

                    bloque_fmt = f"<b>{dia_str}</b> a las {hora_str}"

                    data_notas_tabla.append([
                        Paragraph(bloque_fmt, nota_item_style),
                        Paragraph(actividad_asociada, nota_item_style),
                        Paragraph(texto_nota.replace("\n", "<br/>"), nota_item_style),
                    ])

                tabla_notas = Table(data_notas_tabla, colWidths=[150, 180, 380])
                tabla_notas.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.HexColor("#F8FAFC")],
                        ),
                    ])
                )
                elements.append(tabla_notas)

        doc.build(elements)
        return True
    except Exception as err:
        print(f"Error al generar el PDF: {err}")
        return False


def exportar_a_ics(
    datos_cronograma: Dict[str, Any], nombre_cronograma: str = "Principal"
) -> bool:
    """Genera un archivo .ics con identificadores RFC 5545 válidos para importar en calendarios."""
    archivo_destino = filedialog.asksaveasfilename(
        defaultextension=".ics",
        filetypes=[("Calendario iCalendar", "*.ics")],
        title=f"Exportar {nombre_cronograma} a iCalendar (.ics)",
        initialfile=f"Cronograma_{nombre_cronograma}.ics",
    )

    if not archivo_destino:
        return False

    try:
        cal = Calendar()
        cal.add("prodid", "-//Mi Cronograma Personal//mx//")
        cal.add("version", "2.0")

        dias_mapa = {dia: idx for idx, dia in enumerate(DIAS_ESPANOL)}
        hoy = datetime.now()
        lunes_actual = hoy - timedelta(days=hoy.weekday())

        for clave, valor_raw in datos_cronograma.items():
            actividad = _extraer_texto_actividad(valor_raw)
            if not actividad:
                continue

            partes = clave.split("_")
            if len(partes) != 2:
                continue

            dia_str, hora_str = partes[0], partes[1]

            if dia_str in dias_mapa:
                offset_dias = dias_mapa[dia_str]
                fecha_evento = lunes_actual + timedelta(days=offset_dias)

                try:
                    h_int = int(hora_str.split(":")[0])
                except ValueError:
                    continue

                dt_inicio = datetime(
                    fecha_evento.year,
                    fecha_evento.month,
                    fecha_evento.day,
                    h_int,
                    0,
                    0,
                )
                dt_fin = dt_inicio + timedelta(hours=1)

                evento = Event()
                evento.add("summary", actividad)
                evento.add("dtstart", dt_inicio)
                evento.add("dtend", dt_fin)
                evento.add("dtstamp", datetime.now())
                evento.add("uid", f"{uuid.uuid4()}@cronograma.local")
                evento.add(
                    "description",
                    f"Actividad importada desde el cronograma: {nombre_cronograma}",
                )

                cal.add_component(evento)

        with open(archivo_destino, "wb") as f:
            f.write(cal.to_ical())

        return True
    except Exception as err:
        print(f"Error al generar el archivo .ics: {err}")
        return False