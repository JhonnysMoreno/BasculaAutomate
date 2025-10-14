from PyQt5.QtCore import QThread, pyqtSignal
import csv, os

class CSVWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, ruta, operacion='leer', datos=None):
        super().__init__()
        self.ruta = ruta
        self.operacion = operacion
        self.datos = datos

    def run(self):
        """Ejecuta la operación de lectura o escritura en un hilo separado."""
    
        try:
            if self.operacion == 'leer':
                self._leer_csv()
            elif self.operacion == 'escribir':
                self._escribir_csv()
        except Exception as e:
            self.error.emit(str(e))

    def _leer_csv(self):
        if not os.path.exists(self.ruta):
            self.error.emit(f"El archivo {self.ruta} no existe")
            return
        with open(self.ruta, newline='', encoding='utf-8') as f:
            datos = list(csv.reader(f))
        self.finished.emit(datos)

    def _escribir_csv(self):
        with open(self.ruta, mode='w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerows(self.datos)
        self.finished.emit([])
