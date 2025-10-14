import json
import os
from tkinter import messagebox
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                             QComboBox, QLineEdit, QSlider, QGridLayout,
                             QSpinBox, QSizePolicy, QApplication, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import win32print
from utils.print_manager import PrintManager # Importar PrintManager
from datetime import datetime
from utils.logger_config import setup_logger

CONFIG_FILE = "printer_config.json"

class PrinterConfig(QWidget):
    def __init__(self):
        super().__init__()
        self.logger = setup_logger()
        self.print_manager = PrintManager()
        self.initUI()
        self.load_config()

    def initUI(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Configuración de Impresora", font=QFont("Arial", 16, QFont.Bold)))

        grid = QGridLayout()
        grid.addWidget(QLabel("Impresora:", font=QFont("Arial", 14)), 0, 0)
        self.printer_combo = QComboBox()
        self.populate_printers()
        grid.addWidget(self.printer_combo, 0, 1)
        
        grid.addWidget(QLabel("Titulo:", font=QFont("Arial", 14)), 1, 0)
        self.Titulo = QLineEdit()
        self.Titulo.setMaxLength(50)  # Limita el texto a 50 caracteres
        grid.addWidget(self.Titulo, 1, 1)
        
        grid.addWidget(QLabel("Tamaño Fuentes (General):", font=QFont("Arial", 12)), 2, 0)
        self.size_g_fuentes = QSpinBox()
        self.size_g_fuentes.setMinimum(0)
        self.size_g_fuentes.setMaximum(500)
        grid.addWidget(self.size_g_fuentes, 2, 1)
        
        grid.addWidget(QLabel("Tamaño - Alto (Hoja):", font=QFont("Arial", 12)), 3, 0)
        self.alto_hoja = QSpinBox()
        self.alto_hoja.setMinimum(0)
        self.alto_hoja.setMaximum(500)
        grid.addWidget(self.alto_hoja, 3, 1)
        
        grid.addWidget(QLabel("Tamaño - Ancho (Hoja):", font=QFont("Arial", 12)), 4, 0)
        self.ancho_hoja = QSpinBox()
        self.ancho_hoja.setMinimum(0)
        self.ancho_hoja.setMaximum(500)
        grid.addWidget(self.ancho_hoja, 4, 1)

        # Controles de posición
        grid.addWidget(QLabel("Posición X (Titulo):", font=QFont("Arial", 12)), 5, 0)
        self.x_pos_titulo = QSpinBox()
        self.x_pos_titulo.setMinimum(0)
        self.x_pos_titulo.setMaximum(500)
        grid.addWidget(self.x_pos_titulo, 5, 1)

        grid.addWidget(QLabel("Posición Y (Titulo):", font=QFont("Arial", 12)), 6, 0)
        self.y_pos_titulo = QSpinBox()
        self.y_pos_titulo.setMinimum(0)
        self.y_pos_titulo.setMaximum(500)
        grid.addWidget(self.y_pos_titulo, 6, 1)

        grid.addWidget(QLabel("Posición X (Fecha):", font=QFont("Arial", 12)), 7, 0)
        self.x_pos_fecha = QSpinBox()
        self.x_pos_fecha.setMinimum(0)
        self.x_pos_fecha.setMaximum(500)
        grid.addWidget(self.x_pos_fecha, 7, 1)

        grid.addWidget(QLabel("Posición Y (Fecha):", font=QFont("Arial", 12)), 8, 0)
        self.y_pos_fecha = QSpinBox()
        self.y_pos_fecha.setMinimum(0)
        self.y_pos_fecha.setMaximum(500)
        grid.addWidget(self.y_pos_fecha, 8, 1)
        
        grid.addWidget(QLabel("Posición X (Operario):", font=QFont("Arial", 12)), 9, 0)
        self.x_pos_operario = QSpinBox()
        self.x_pos_operario.setMinimum(0)
        self.x_pos_operario.setMaximum(500)
        grid.addWidget(self.x_pos_operario, 9, 1)

        grid.addWidget(QLabel("Posición Y (Operario):", font=QFont("Arial", 12)), 10, 0)
        self.y_pos_operario = QSpinBox()
        self.y_pos_operario.setMinimum(0)
        self.y_pos_operario.setMaximum(500)
        grid.addWidget(self.y_pos_operario, 10, 1)

        grid.addWidget(QLabel("Posición X (Producto):", font=QFont("Arial", 12)), 11, 0)
        self.x_pos_producto = QSpinBox()
        self.x_pos_producto.setMinimum(0)
        self.x_pos_producto.setMaximum(500)
        grid.addWidget(self.x_pos_producto, 11, 1)

        grid.addWidget(QLabel("Posición Y (Producto):", font=QFont("Arial", 12)), 12, 0)
        self.y_pos_producto = QSpinBox()
        self.y_pos_producto.setMinimum(0)
        self.y_pos_producto.setMaximum(500)
        grid.addWidget(self.y_pos_producto, 12, 1)

        grid.addWidget(QLabel("Posición X (Nombre Producto):", font=QFont("Arial", 12)), 13, 0)
        self.x_pos_nombre_pro = QSpinBox()
        self.x_pos_nombre_pro.setMinimum(0)
        self.x_pos_nombre_pro.setMaximum(500)
        grid.addWidget(self.x_pos_nombre_pro, 13, 1)

        grid.addWidget(QLabel("Posición Y (Nombre Producto):", font=QFont("Arial", 12)), 14, 0)
        self.y_pos_nombre_pro = QSpinBox()
        self.y_pos_nombre_pro.setMinimum(0)
        self.y_pos_nombre_pro.setMaximum(500)
        grid.addWidget(self.y_pos_nombre_pro, 14, 1)
        
        grid.addWidget(QLabel("Posición X (Cantidad):", font=QFont("Arial", 12)), 15, 0)
        self.x_pos_cantidad = QSpinBox()
        self.x_pos_cantidad.setMinimum(0)
        self.x_pos_cantidad.setMaximum(500)
        grid.addWidget(self.x_pos_cantidad, 15, 1)
        
        grid.addWidget(QLabel("Posición Y (Cantidad):", font=QFont("Arial", 12)), 16, 0)
        self.y_pos_cantidad = QSpinBox()
        self.y_pos_cantidad.setMinimum(0)
        self.y_pos_cantidad.setMaximum(500)
        grid.addWidget(self.y_pos_cantidad, 16, 1)
        
        grid.addWidget(QLabel("Posición X (Peso):", font=QFont("Arial", 12)), 17, 0)
        self.x_pos_peso = QSpinBox()
        self.x_pos_peso.setMinimum(0)
        self.x_pos_peso.setMaximum(500)
        grid.addWidget(self.x_pos_peso, 17, 1)

        grid.addWidget(QLabel("Posición Y (Peso):", font=QFont("Arial", 12)), 18, 0)
        self.y_pos_peso = QSpinBox()
        self.y_pos_peso.setMinimum(0)
        self.y_pos_peso.setMaximum(500)
        grid.addWidget(self.y_pos_peso, 18, 1)
        
        
        layout.addLayout(grid)

        # Botón para guardar la configuración
        save_button = QPushButton("Guardar Configuración", font=QFont("Arial", 12))
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)

        # Widget para mostrar la vista previa
        self.preview_label = QLabel()
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label)

        # Botón para generar la vista previa
        preview_button = QPushButton("Generar Vista Previa", font=QFont("Arial", 12))
       # preview_button.clicked.connect(self.generate_preview)
        layout.addWidget(preview_button)

        self.setLayout(layout)

    def populate_printers(self):
        try:
            printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)
           # print(f"Impresoras encontradas: {printers}")
            for printer_tuple in printers:
                try:
                    if isinstance(printer_tuple, tuple) and len(printer_tuple) >= 3:
                        printer = printer_tuple[2]
                        if isinstance(printer, dict):
                            self.printer_combo.addItem(str(printer.get("pDisplayName", "N/A")))
                            QApplication.processEvents()
                        elif isinstance(printer, str):
                            self.printer_combo.addItem(printer)
                            QApplication.processEvents()
                    else:
                        print(f"Elemento inesperado en la lista de impresoras (no es tupla): {printer_tuple}")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al agregar impresora a la lista: {e}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener la lista de impresoras: {e}")
    
    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Asigna la impresora
                    self.printer_combo.setCurrentText(config.get("printer", ""))
                    self.Titulo.setText(config.get("Titulo", ""))
                    self.size_g_fuentes.setValue(int(config.get("SizeG_Fuentes", 0)))
                    # Tamaño del papel
                    self.alto_hoja.setValue(int(config.get("Alto_Hoja", 0)))
                    self.ancho_hoja.setValue(int(config.get("Ancho_Hoja", 0)))
                    # Extrae las posiciones de los campos
                    campos = config.get("campos", {})
                    self.x_pos_titulo.setValue(campos.get("titulo", {}).get("x", 0))
                    self.y_pos_titulo.setValue(campos.get("titulo", {}).get("y", 0))
                    self.x_pos_fecha.setValue(campos.get("fecha", {}).get("x", 0))
                    self.y_pos_fecha.setValue(campos.get("fecha", {}).get("y", 0))
                    self.x_pos_operario.setValue(campos.get("operario", {}).get("x", 0))
                    self.y_pos_operario.setValue(campos.get("operario", {}).get("y", 0))
                    self.x_pos_producto.setValue(campos.get("codigo_producto", {}).get("x", 0))
                    self.y_pos_producto.setValue(campos.get("codigo_producto", {}).get("y", 0))
                    self.x_pos_nombre_pro.setValue(campos.get("nombre_producto", {}).get("x", 0))
                    self.y_pos_nombre_pro.setValue(campos.get("nombre_producto", {}).get("y", 0))
                    self.x_pos_cantidad.setValue(campos.get("cantidad", {}).get("x", 0))
                    self.y_pos_cantidad.setValue(campos.get("cantidad", {}).get("y", 0))
                    self.x_pos_peso.setValue(campos.get("peso", {}).get("x", 0))
                    self.y_pos_peso.setValue(campos.get("peso", {}).get("y", 0))
                                        
                    print("Configuración cargada correctamente.")
        
        except Exception as e:
            print(f"Error al cargar la configuración: {e}")
    
    def save_config(self):
        try:
            config = {
                "printer": self.printer_combo.currentText(),
                "Titulo": self.Titulo.text(),
                "SizeG_Fuentes": self.size_g_fuentes.value(),
                "Alto_Hoja": self.alto_hoja.value(),
                "Ancho_Hoja": self.ancho_hoja.value(),
                
                "campos": {
                    "titulo": {
                        "x": self.x_pos_titulo.value(),
                        "y": self.y_pos_titulo.value()
                        },
                    "fecha": { 
                        "x": self.x_pos_fecha.value(),
                        "y": self.y_pos_fecha.value()
                        },
                    "operario": {
                        "x": self.x_pos_operario.value(),
                        "y": self.y_pos_operario.value()
                        },
                    "codigo_producto": {
                        "x": self.x_pos_producto.value(),
                        "y": self.y_pos_producto.value()
                        },
                    "nombre_producto": {
                        "x": self.x_pos_nombre_pro.value(),
                        "y": self.y_pos_nombre_pro.value()
                        },
                     "cantidad": {
                        "x": self.x_pos_cantidad.value(),
                        "y": self.y_pos_cantidad.value()
                        },
                    "peso": {
                        "x": self.x_pos_peso.value(),
                        "y": self.y_pos_peso.value()
                        }
                    }
            }
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            
            QMessageBox.information(self, "Configuración", "Configuración guardada correctamente.")
        
            
        except Exception as e:
            print(f"Error al guardar la configuración: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo guardar la configuración:\n{e}")


    def generate_preview(self):
        try:
            print("Generando vista previa...")
            config = self.get_config()
            printer_name = config.get("printer", self.print_manager.get_default_printer())
            self.print_manager.printer_name = printer_name

            preview_text = self.print_manager.generate_preview(
                operario="Operario XXXXXX",
                cantidad="XXXXXX",
                producto="PRODXXXXXXXXXXXX",
                nombre_producto="Producto XXXXXXXXXXXXXXXXXX",
                peso="XXXXXX kg",
                fecha=datetime.now().strftime("%d/%m/%Y"),
                config=config
            )

            self.preview_label.setText(preview_text)
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar la vista previa: {e}")