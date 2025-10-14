from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QMessageBox)
from PyQt5.QtCore import Qt
import csv
import os
from utils.logger_config import setup_logger

class HistorialWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historial de Registros")
        self.resize(1000, 600)
        self.logger = setup_logger()
        
        # Archivo de registros
        self.csv_file = 'data/Datos_bascula.csv'
        
        # Inicializar interfaz
        self.init_ui()
        self.cargar_registros()

    def init_ui(self):
        central = QWidget()
        layout = QVBoxLayout()

        # Título
        titulo = QLabel("Historial de Registros")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(titulo)

        # Tabla de historial
        self.tabla_historial = QTableWidget()
        self.tabla_historial.setColumnCount(6)
        self.tabla_historial.setHorizontalHeaderLabels(['Fecha/Hora', 'Operario', 'Cédula', 'Producto', 'Cantidad', 'Peso (kg)'])
        self.tabla_historial.horizontalHeader().setStretchLastSection(True)
        self.tabla_historial.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_historial.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_historial.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.tabla_historial)

        # Botones
        btn_layout = QHBoxLayout()
        self.btn_actualizar = QPushButton("Actualizar")
        self.btn_actualizar.clicked.connect(self.cargar_registros)
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.clicked.connect(self.close)
        
        btn_layout.addWidget(self.btn_actualizar)
        btn_layout.addWidget(self.btn_cerrar)
        layout.addLayout(btn_layout)

        central.setLayout(layout)
        self.setCentralWidget(central)

    def cargar_registros(self):
        """Carga todos los registros del archivo CSV en la tabla."""
        try:
            if not os.path.exists(self.csv_file):
                QMessageBox.warning(self, "Error", "No existe el archivo de registros")
                return

            # Verificar si el archivo está vacío
            if os.path.getsize(self.csv_file) == 0:
                self.tabla_historial.setRowCount(0)
                self.logger.info("El archivo de registros está vacío")
                return

            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                registros = list(reader)
                
                # Verificar si hay datos además de los encabezados
                if len(registros) <= 1:  # Solo encabezados o archivo vacío
                    self.tabla_historial.setRowCount(0)
                    self.logger.info("No hay registros en el archivo")
                    return

                # Configurar tabla
                self.tabla_historial.setRowCount(len(registros) - 1)  # Excluir encabezados
                
                # Llenar tabla (excluyendo encabezados)
                for row, registro in enumerate(registros[1:]):
                    for col, valor in enumerate(registro):
                        item = QTableWidgetItem(str(valor))  # Asegurar que el valor sea string
                        self.tabla_historial.setItem(row, col, item)

                # Ordenar por fecha (más reciente primero)
                self.tabla_historial.sortItems(0, Qt.DescendingOrder)
                
                self.logger.info("Historial de registros cargado correctamente")

        except Exception as e:
            self.logger.error(f"Error al cargar registros: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error al cargar registros: {str(e)}")
            self.tabla_historial.setRowCount(0)  # Limpiar la tabla en caso de error 