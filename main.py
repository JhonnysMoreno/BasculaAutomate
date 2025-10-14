# main.py
import sys
from PyQt5.QtWidgets import QApplication # type: ignore
from gui.main_windows import BasculaApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Estilo más moderno
    ventana = BasculaApp()
    ventana.showMaximized()
   # ventana.show() 
    sys.exit(app.exec_())