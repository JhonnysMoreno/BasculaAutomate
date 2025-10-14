from PyQt5.QtWidgets import (
    QDialog, QTabWidget, QVBoxLayout, QWidget, QPushButton,
    QFileDialog, QTableWidget, QTableWidgetItem, QHBoxLayout,
    QMessageBox, QProgressBar
)
from utils.logger_config import setup_logger
from gui.admin_window_printer_config import PrinterConfig
from core.core_panel_admin.logic_operarios import LogicOperarios
from core.core_panel_admin.logic_productos import LogicProductos
from core.core_panel_admin.worker.csv_service import CSVService
from core.core_panel_admin.worker.csv_worker import CSVWorker

import os

class AdminPanel(QDialog):
    """
    Panel de administración que permite gestionar operarios y productos.
    Proporciona una interfaz gráfica para cargar, editar y guardar datos en archivos CSV.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Panel Administrador")
        self.setMinimumSize(1000, 700)
        self.logger = setup_logger()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.tab_operarios = QWidget()
        self.tab_productos = QWidget()
        self.tab_impresoras = QWidget()

        try:
            self.config_impresora = PrinterConfig()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar impresoras: {e}")
            return

        self.tab_impresoras.setLayout(QVBoxLayout())
        self.tab_impresoras.layout().addWidget(self.config_impresora)

        self.init_tab_operarios()
        self.init_tab_productos()

        self.tabs.addTab(self.tab_operarios, "Operarios")
        self.tabs.addTab(self.tab_productos, "Productos")
        self.tabs.addTab(self.tab_impresoras, "Administración de Impresoras")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    # --- OPERARIOS ---
    def init_tab_operarios(self):
        layout = QVBoxLayout()
        self.tabla_operarios = QTableWidget()
        self.tabla_operarios.setColumnCount(2)
        self.tabla_operarios.setHorizontalHeaderLabels(["Nombre", "Cédula"])
        layout.addWidget(self.tabla_operarios)

        self.progress_operarios = QProgressBar()
        layout.addWidget(self.progress_operarios)

        botones = QHBoxLayout()
        self.btn_cargar_op = QPushButton("Cargar CSV")
        self.btn_guardar_op = QPushButton("Guardar CSV")
        self.btn_eliminar_op = QPushButton("Eliminar fila")
        botones.addWidget(self.btn_cargar_op)
        botones.addWidget(self.btn_guardar_op)
        botones.addWidget(self.btn_eliminar_op)
        layout.addLayout(botones)
        self.tab_operarios.setLayout(layout)

        CSVService.ensure_csv_exists("data/operarios.csv", ["Nombre", "Cédula"])
        self.cargar_operarios("data/operarios.csv")

        self.btn_cargar_op.clicked.connect(lambda: self.cargar_operarios_dialogo())
        self.btn_guardar_op.clicked.connect(self.guardar_operarios)
        self.btn_eliminar_op.clicked.connect(lambda: self.eliminar_fila(self.tabla_operarios))

    def cargar_operarios_dialogo(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar CSV", "", "Archivos CSV (*.csv)")
        if ruta:
            self.cargar_operarios(ruta)

    def cargar_operarios(self, ruta):
        self.worker = CSVWorker(ruta, 'leer')
        self.worker.finished.connect(self.actualizar_tabla_operarios)
        self.worker.error.connect(lambda e: QMessageBox.critical(self, "Error", e))
        self.worker.start()

    def actualizar_tabla_operarios(self, datos):
        self.tabla_operarios.setRowCount(len(datos))
        for i, fila in enumerate(datos):
            for j, valor in enumerate(fila):
                self.tabla_operarios.setItem(i, j, QTableWidgetItem(valor))

    def guardar_operarios(self):
        datos = [
            [self.tabla_operarios.item(i, 0).text(), self.tabla_operarios.item(i, 1).text()]
            for i in range(self.tabla_operarios.rowCount())
            if self.tabla_operarios.item(i, 0) and self.tabla_operarios.item(i, 1)
        ]
        try:
            LogicOperarios.validar_cedulas_unicas(datos)
            LogicOperarios.guardar_operarios("data/operarios.csv", datos)
            QMessageBox.information(self, "Éxito", "Datos guardados correctamente.")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    # --- PRODUCTOS ---
    def init_tab_productos(self):
        layout = QVBoxLayout()
        self.tabla_productos = QTableWidget()
        self.tabla_productos.setColumnCount(2)
        self.tabla_productos.setHorizontalHeaderLabels(["Código", "Nombre del producto"])
        layout.addWidget(self.tabla_productos)

        self.progress_productos = QProgressBar()
        layout.addWidget(self.progress_productos)

        botones = QHBoxLayout()
        self.btn_cargar_prod = QPushButton("Cargar CSV")
        self.btn_guardar_prod = QPushButton("Guardar CSV")
        self.btn_eliminar_prod = QPushButton("Eliminar fila")
        botones.addWidget(self.btn_cargar_prod)
        botones.addWidget(self.btn_guardar_prod)
        botones.addWidget(self.btn_eliminar_prod)
        layout.addLayout(botones)
        self.tab_productos.setLayout(layout)

        CSVService.ensure_csv_exists("data/productos.csv", ["Código", "Nombre del producto"])
        self.cargar_productos("data/productos.csv")

        self.btn_cargar_prod.clicked.connect(lambda: self.cargar_productos_dialogo())
        self.btn_guardar_prod.clicked.connect(self.guardar_productos)
        self.btn_eliminar_prod.clicked.connect(lambda: self.eliminar_fila(self.tabla_productos))

    def cargar_productos_dialogo(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar CSV", "", "Archivos CSV (*.csv)")
        if ruta:
            self.cargar_productos(ruta)

    def cargar_productos(self, ruta):
        self.worker = CSVWorker(ruta, 'leer')
        self.worker.finished.connect(self.actualizar_tabla_productos)
        self.worker.error.connect(lambda e: QMessageBox.critical(self, "Error", e))
        self.worker.start()

    def actualizar_tabla_productos(self, datos):
        self.tabla_productos.setRowCount(len(datos))
        for i, fila in enumerate(datos):
            for j, valor in enumerate(fila):
                self.tabla_productos.setItem(i, j, QTableWidgetItem(valor))

    def guardar_productos(self):
        datos = [
            [self.tabla_productos.item(i, 0).text(), self.tabla_productos.item(i, 1).text()]
            for i in range(self.tabla_productos.rowCount())
            if self.tabla_productos.item(i, 0) and self.tabla_productos.item(i, 1)
        ]
        LogicProductos.guardar_productos("data/productos.csv", datos)
        QMessageBox.information(self, "Éxito", "Productos guardados correctamente.")

    # --- UTIL ---
    def eliminar_fila(self, tabla):
        fila = tabla.currentRow()
        if fila >= 0:
            tabla.removeRow(fila)
        else:
            QMessageBox.information(self, "Eliminar", "Selecciona una fila para eliminar.")