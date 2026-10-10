import threading
from PIL import Image, ImageDraw  # type: ignore

try:
  import pystray  # type: ignore

  PYSTRAY_DISPONIBLE = True
except ImportError:
  PYSTRAY_DISPONIBLE = False


def crear_imagen_icono():
  """Genera un icono ligero en memoria para la bandeja del sistema."""
  imagen = Image.new("RGB", (64, 64), color="#181825")
  d = ImageDraw.Draw(imagen)
  d.rectangle([12, 12, 52, 52], outline="#89B4FA", width=3)
  d.rectangle([22, 22, 42, 42], fill="#7AA2F7")
  return imagen


def mostrar_ventana(icon, item, ventana):
  """Detiene el icono de la bandeja y restaura la ventana principal."""
  if icon:
    icon.stop()
  ventana.after(0, ventana.deiconify)


def cerrar_aplicacion_total(icon=None, item=None, ventana=None):
  """Cierra limpiamente tanto el icono de la bandeja como la ventana principal."""
  if icon:
    icon.stop()
  if ventana:
    ventana.after(0, ventana.destroy)


def ocultar_a_bandeja(ventana):
  """Oculta la ventana principal y activa el icono en la bandeja."""
  if not PYSTRAY_DISPONIBLE:
    ventana.destroy()
    return

  ventana.withdraw()

  menu = pystray.Menu(
      pystray.MenuItem(
          "Mostrar Cronograma",
          lambda i, item: mostrar_ventana(i, item, ventana),
      ),
      pystray.MenuItem(
          "Salir por completo",
          lambda i, item: cerrar_aplicacion_total(i, item, ventana),
      ),
  )

  imagen = crear_imagen_icono()
  icono_tray = pystray.Icon("Cronograma", imagen, "Cronograma Dinámico", menu)

  threading.Thread(target=icono_tray.run, daemon=True).start()