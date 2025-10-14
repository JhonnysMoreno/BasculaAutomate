from email.mime import application
import os
import csv
import sys
import serial
import serial.tools.list_ports
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
                             QHBoxLayout, QComboBox, QLineEdit, QMessageBox, QSpacerItem,
                             QSizePolicy, QDialog, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import QTimer, QDateTime, Qt
from PyQt5.QtGui import QFont
from utils.logger_config import setup_logger
from gui.historial_window import HistorialWindow
from utils.print_manager import PrintManager


class BasculaApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Báscula Industrial Koen Pack")
        self.setMinimumSize(1000, 800)
        self.serial = None
        self.print_manager = PrintManager()
        
        # Referencias para evitar ventanas duplicadas
        self.admin_login_dialog = None
        self.admin_panel_window = None

        # Inicializar tabla_historial antes de cualquier otra operación
        self.tabla_historial = QTableWidget()
        self.tabla_historial.setColumnCount(6)
        self.tabla_historial.setHorizontalHeaderLabels(['Fecha/Hora', 'Operario', 'Cédula', 'Producto', 'Cantidad', 'Peso (kg)'])
        

        # Configurar logger
        self.logger = setup_logger()
        self.logger.info("Iniciando aplicación de báscula industrial")

        # Buffer simple para peso
        self.buffer_peso = ""

        #Temporizador de inactividad
        self.inactivity_timer = QTimer()
        self.inactivity_timer.setInterval(5 * 60 * 1000)  # 5 minutos
        self.inactivity_timer.timeout.connect(self.auto_disconnect)

        self.csv_file = 'data/Datos_bascula.csv' # Archivo principal para guardar registros
        self.operarios_file = 'data/operarios.csv' # Archivo de operarios
        self.productos_file = 'data/productos.csv'  # Archivo de productos
        self.operarios_dict = {}  # Diccionario nombre->cédula
        self.productos_dict = {}  # Diccionario nombre->código

        #Inicialización de componentes
        self.init_ui()
        self.init_csv() # Prepara archivos CSV y Carga Listas
        self.update_ports()

        #Temporizador de lectura de peso - reducido a 100ms
        self.timer = QTimer()
        self.timer.setInterval(100)  # 100ms = 0.1 segundos
        self.timer.timeout.connect(self.leer_peso)
        self.is_connected = False
        

    def init_ui(self):
        central = QWidget()
        layout = QVBoxLayout()

        # Selector de Puerto
        port_layout = QHBoxLayout()
        port_label = QLabel("Puerto COM:")
        port_label.setFont(QFont("Arial", 12))
        self.port_combo = QComboBox() # Lista de puertos COM
        self.port_combo.setFont(QFont("Arial", 12))
        self.refresh_ports_btn = QPushButton("Actualizar Puertos")
        self.refresh_ports_btn.setFont(QFont("Arial", 12))
        self.connect_btn = QPushButton("Conectar")
        self.connect_btn.setFont(QFont("Arial", 12))
        self.connect_btn.clicked.connect(self.connect_serial) # Conecta al puerto seleccionado
        self.refresh_ports_btn.clicked.connect(self.update_ports) # Botón para refrescar puertos
        
        

        # Agrega widgets de puerto
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_combo)
        port_layout.addWidget(self.refresh_ports_btn)
        port_layout.addWidget(self.connect_btn)
        layout.addLayout(port_layout)

        # Visualizador de peso
        self.lbl_peso = QLabel("0.00 Kg")
        self.lbl_peso.setAlignment(Qt.AlignCenter)
        self.lbl_peso.setFont(QFont("Arial", 76, QFont.Bold))
        layout.addWidget(self.lbl_peso)
        
        self.lbl_ultimo = QLabel("Último Registro: -")
        self.lbl_ultimo.setFont(QFont("Arial", 12))
        layout.addWidget(self.lbl_ultimo)

        #  operario + cédula + producto
        self.cmb_operarios = QComboBox()
        self.cmb_operarios.setFont(QFont("Arial", 12))
        self.cmb_operarios.setEditable(True)
        self.cmb_operarios.setPlaceholderText("Selecciona o escribe nombre de un operario")
        self.cmb_operarios.currentTextChanged.connect(self.actualizar_cedula_operario)

        self.txt_cedula = QLineEdit()
        self.txt_cedula.setFont(QFont("Arial", 12))
        self.txt_cedula.setPlaceholderText("Cédula (solo números)")
        self.txt_cedula.setMaxLength(10)

        self.cmb_productos = QComboBox()
        self.cmb_productos.setFont(QFont("Arial", 12))
        self.cmb_productos.setEditable(True)
        self.cmb_productos.setPlaceholderText("Selecciona o escribe código de un producto")
        self.cmb_productos.currentTextChanged.connect(self.actualizar_nombre_producto)

        self.txt_nombre_pro = QLineEdit()
        self.txt_nombre_pro.setFont(QFont("Arial", 12))
        self.txt_nombre_pro.setPlaceholderText("Nombre del producto")
        self.txt_nombre_pro.setMaxLength(50)
        
        self.txt_cantidad = QLineEdit()
        self.txt_cantidad.setFont(QFont("Arial", 12))
        self.txt_cantidad.setPlaceholderText("(Ingrese solo valores numéricos)")

        # Botones de acción
        self.clearCampos = QPushButton("Limpiar Campos") #Botón para limpiar campos
        self.clearCampos.setFont(QFont("Arial", 12))
        self.clearCampos.clicked.connect(self.limpiar_campos)
        
        self.btn_guardar = QPushButton("Guardar Registro")
        self.btn_guardar.setFont(QFont("Arial", 12))
        self.btn_guardar.clicked.connect(self.guardar_registro)
        self.btn_guardar.setStyleSheet("background-color: green; color: white;")

        self.btn_imprimir = QPushButton("Imprimir Ticket")
        self.btn_imprimir.setFont(QFont("Arial", 12))
        self.btn_imprimir.clicked.connect(self.imprimir_ticket)
        self.btn_imprimir.setEnabled(False)  # Deshabilitado inicialmente

        self.btn_cerrar = QPushButton("Cerrar Programa")
        self.btn_cerrar.setFont(QFont("Arial", 12))
        self.btn_cerrar.clicked.connect(self.cerrar_programa)
        
        # Botón de Administrador
        self.btn_admin = QPushButton("Modo Administrador")
        self.btn_admin.setFont(QFont("Arial", 12))
        self.btn_admin.clicked.connect(self.abrir_login_admin)

        self.btn_historial = QPushButton("Ver Historial")
        self.btn_historial.setFont(QFont("Arial", 12))
        self.btn_historial.clicked.connect(self.abrir_historial)

        # Agregar el nuevo botón de backup
        self.btn_backup = QPushButton("Exportar Registros")
        self.btn_backup.setFont(QFont("Arial", 12))
        self.btn_backup.clicked.connect(self.exportar_backup)

        row2 = QHBoxLayout()
        operario_label = QLabel("Operario:")
        operario_label.setFont(QFont("Arial", 12))
        row2.addWidget(operario_label)
        row2.addWidget(self.cmb_operarios)
        cedula_label = QLabel("Cédula:")
        cedula_label.setFont(QFont("Arial", 12))
        row2.addWidget(cedula_label)
        row2.addWidget(self.txt_cedula)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        producto_label = QLabel("Producto:")
        producto_label.setFont(QFont("Arial", 12))
        row3.addWidget(producto_label)
        row3.addWidget(self.cmb_productos)
        nombre_pro_label = QLabel("Nombre del producto:")
        nombre_pro_label.setFont(QFont("Arial", 12))
        row3.addWidget(nombre_pro_label)
        row3.addWidget(self.txt_nombre_pro)
        txt_cantidad = QLabel("Cantidad:")
        txt_cantidad.setFont(QFont("Arial", 12))
        row3.addWidget(txt_cantidad)
        row3.addWidget(self.txt_cantidad)
        layout.addLayout(row3)

        # Reducir el espaciador vertical para minimizar el espacio al final
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        row4 = QHBoxLayout()
        row4.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        row4.addWidget(self.clearCampos)
        row4.addItem(QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))
        row4.addWidget(self.btn_guardar)
        row4.addItem(QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)) # pequeño espaciador horizontal entre los botones
        row4.addWidget(self.btn_imprimir)
        row4.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addLayout(row4)

        # Reducir el espaciador vertical para minimizar el espacio al final
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        row4_5 = QHBoxLayout()
        row4_5.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        row4_5.addWidget(self.btn_cerrar)
        layout.addLayout(row4_5)

        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # botón de administrador + historial + backup
        row5 = QHBoxLayout()
        row5.addWidget(self.btn_admin)
        row5.addItem(QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))
        row5.addWidget(self.btn_historial)
        row5.addItem(QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))
        row5.addWidget(self.btn_backup)
        layout.addLayout(row5)

        layout.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        row6 = QHBoxLayout()
        copyright_label = QLabel("© Desarrollado por: Koen Pack Colombia IT")
        copyright_label.setFont(QFont("Arial", 8))  # Fuente 
        copyright_label.setStyleSheet("color: #666666;")  # Color gris
        copyright_label.setMaximumSize(350, 20)  # Tamaño fijo
        copyright_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)  # Alineado a la derecha y abajo
        row6.addWidget(copyright_label)
        copyright_label2 = QLabel("Support Admin: @y.moreno@koenpack.com")
        copyright_label2.setFont(QFont("Arial", 8))  # Fuente 
        copyright_label2.setStyleSheet("color: #666666;")  # Color gris
        copyright_label2.setMaximumSize(350, 20)  # Tamaño fijo
        copyright_label2.setAlignment(Qt.AlignRight | Qt.AlignBottom)  # Alineado a la derecha y abajo
        row6.addWidget(copyright_label2)
        layout.addLayout(row6)

        central.setLayout(layout)
        self.setCentralWidget(central)

    
    def update_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)


    def connect_serial(self):
        port = self.port_combo.currentText()
        # Si ya está conectado y el puerto sigue abierto 
        if self.is_connected and self.serial and self.serial.is_open:
            self.serial.close()
            self.timer.stop()
            self.inactivity_timer.stop() 
            self.is_connected = False
            self.connect_btn.setText("Conectar")
            self.connect_btn.setStyleSheet("background-color: green; color: white;")
            self.lbl_peso.setText("0.00 Kg")  # Resetear peso al desconectar
            self.logger.info(f"Desconectado del puerto {port}")
            QMessageBox.information(self, "Desconectado", "Puerto cerrado correctamente.")
            return

        try:
            # Intento de abrir el puerto serial
            self.serial = serial.Serial(port, 9600, timeout=1)
            if self.serial.is_open:  # Verificamos si realmente se abrió 
                self.timer.start()
                self.inactivity_timer.start()
                self.is_connected = True
                self.connect_btn.setText("Desconectar")
                self.connect_btn.setStyleSheet("background-color: red; color: white;")
                self.lbl_peso.setText("0.00 Kg")  # Resetear peso al conectar
                self.logger.info(f"Conectado al puerto {port}")
                QMessageBox.information(self, "Conectado", f"Conectado al puerto {port}")
            else:
                raise serial.SerialException("El puerto no se abrió correctamente.")
        except serial.SerialException as e:
            # Errores específicos de pyserial (puerto inexistente, en uso, permiso denegado, etc.)
            self.is_connected = False
            self.connect_btn.setText("Conectar")
            self.connect_btn.setStyleSheet("background-color: green; color: white;")
            self.lbl_peso.setText("0.00 Kg")
            self.logger.error(f"Error al conectar al puerto {port}: {str(e)}")
            QMessageBox.critical(
                self,
                "Error de conexión serial",
                f"No se pudo abrir el puerto {port}:\nComprueba que el puerto existe y que ningún otro programa lo esté usando."
            )
        except OSError as e:
            # Manejar errores de SO (ej. Semaphore timeout / código WinError 121)
            self.is_connected = False
            self.connect_btn.setText("Conectar")
            self.connect_btn.setStyleSheet("background-color: green; color: white;")
            self.lbl_peso.setText("0.00 Kg")
            win_msg = str(e)
            if getattr(e, "winerror", None) == 121 or "Semaphore" in win_msg or "tiempo de espera" in win_msg.lower():
                detalle = (
                    "Tiempo de espera del sistema al abrir el puerto (Semaphore timeout).\n"
                    "Posibles acciones: reiniciar dispositivo/báscula, desconectar/volver a conectar el cable,\n"
                    "probar otro puerto COM."
                )
            else:
                detalle = win_msg
            self.logger.error(f"Error al conectar al puerto {port}: {win_msg}")
            QMessageBox.critical(
                self,
                "Error de sistema al abrir puerto",
                f"No se pudo abrir el puerto {port}:\n{detalle}"
            )
        except Exception as e:
            # Captura cualquier otro error inesperado
            self.is_connected = False
            self.connect_btn.setText("Conectar")
            self.connect_btn.setStyleSheet("background-color: green; color: white;")
            self.lbl_peso.setText("0.00 Kg")
            self.logger.error(f"Error al conectar al puerto {port}: {str(e)}")
            QMessageBox.critical(self, "Error", f"No se pudo conectar al puerto: {e}")

    # auto_disconnect(): desconecta por inactividad
    def auto_disconnect(self):
         if self.is_connected and self.serial and self.serial.is_open:
            self.serial.close()
            self.timer.stop()
            self.inactivity_timer.stop() 
            self.is_connected = False
            self.connect_btn.setText("Conectar")
            self.connect_btn.setStyleSheet("background-color: green; color: white;")
            self.lbl_peso.setText("0.00 Kg")  # Resetear peso al desconectar por inactividad
            self.logger.info("Desconectado por inactividad")
            QMessageBox.information(self, "Desconectado", "Puerto cerrado por inactividad.")
            



    def leer_peso(self):
        try:
            if self.serial and self.serial.is_open:
                try:
                    if self.serial.in_waiting:
                        # Leer datos y agregar al buffer
                        datos = self.serial.readline().decode('utf-8').strip()
                        if datos:
                            # Extraer solo el valor numérico del peso
                            # Eliminar ST, GS, + y cualquier otro carácter no numérico excepto el punto decimal
                            peso_limpio = ''.join(c for c in datos if c.isdigit() or c == '.')
                            if peso_limpio:  # Solo actualizar si hay un valor numérico
                                self.buffer_peso = peso_limpio
                                self.lbl_peso.setText(f"{self.buffer_peso} Kg")
                            # Programar siguiente lectura inmediatamente
                            QTimer.singleShot(0, self.leer_peso)
                except serial.SerialException as e:
                    self.logger.error(f"Error de comunicación serial: {str(e)}")
                    self.desconectar_puerto()
                    QMessageBox.warning(
                        self,
                        "Error de Comunicación",
                        "Se perdió la conexión con la báscula. Por favor, reconecte el dispositivo y vuelva a conectar."
                    )
                except Exception as e:
                    self.logger.error(f"Error inesperado al leer peso: {str(e)}")
                    self.desconectar_puerto()
        except Exception as e:
            self.logger.error(f"Error general en leer_peso: {str(e)}")
            self.desconectar_puerto()

    def desconectar_puerto(self):
        """Método para manejar la desconexión segura del puerto"""
        try:
            if self.serial and self.serial.is_open:
                self.serial.close()
        except Exception as e:
            self.logger.error(f"Error al cerrar el puerto: {str(e)}")
        finally:
            self.serial = None
            self.connect_btn.setText("Conectar")
            self.connect_btn.setEnabled(True)
            self.port_combo.setEnabled(True)
            self.lbl_peso.setText("0.00 Kg")


    def init_csv(self):
        # Verificar y crear el archivo CSV principal si no existe
        self.crear_archivo_si_no_existe(self.csv_file, ['FechaHora', 'Operario', 'Cédula', 'Producto', 'Cantidad', 'Peso'])
        
        # Cargar operarios y actualizar la lista desplegable
        self.cargar_operarios()
        self.cmb_operarios.clear()  # Limpiar la lista desplegable antes de actualizar
        self.actualizar_lista_desplegable(self.operarios_file, self.cmb_operarios)
        
        self.cargar_productos()
        self.cmb_productos.clear()  # Limpiar la lista desplegable antes de actualizar
        self.actualizar_lista_desplegable(self.productos_file, self.cmb_productos)

        # Cargar último registro
        self.cargar_ultimo_registro()

    def crear_archivo_si_no_existe(self, ruta, encabezados):
        # Asegurarse de que el directorio exista
        directorio = os.path.dirname(ruta)
        if not os.path.exists(directorio):
            os.makedirs(directorio)
            
        if not os.path.exists(ruta):
            with open(ruta, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(encabezados)

    def actualizar_lista_desplegable(self, archivo, combo_box):
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        combo_box.addItem(row[0])
        except FileNotFoundError:
            with open(archivo, 'w', encoding='utf-8') as f:
                pass
        

                
# load_operarios(): carga operarios y sus cédulas
    def cargar_operarios(self):
        try:
            with open(self.operarios_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) == 2:
                        nombre, cedula = row
                        self.operarios_dict[nombre] = cedula
                        self.cmb_operarios.addItem(nombre)
        except FileNotFoundError:
            with open(self.operarios_file, 'w', encoding='utf-8') as f:
                pass
    
        
    
    # agregar_operario(): agrega operario al archivo
    def agregar_operario(self, nombre, cedula):
        with open(self.operarios_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([nombre, cedula])
            self.operarios_dict[nombre] = cedula
            self.cmb_operarios.addItem(nombre)

    def actualizar_cedula_operario(self, text):
        cedula = self.operarios_dict.get(text.strip(), '')
        self.txt_cedula.setText(cedula)

    def actualizar_nombre_producto(self, text):
        nombre_pro = self.productos_dict.get(text.strip(), '')
        self.txt_nombre_pro.setText(nombre_pro)

     # cargar_productos(): carga productos
    def cargar_productos(self):
        try:
            with open(self.productos_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) == 2:
                        nombre_pro, codigo = row
                        self.productos_dict[nombre_pro] = codigo
                        self.cmb_productos.addItem(nombre_pro)
        except FileNotFoundError:
            with open(self.productos_file, 'w', encoding='utf-8') as f:
                pass
    
    def agregar_producto(self, nombre_pro, codigo):
        with open(self.productos_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([nombre_pro, codigo])
            self.productos_dict[nombre_pro] = codigo
            self.cmb_productos.addItem(nombre_pro)
    


    def cargar_ultimo_registro(self):
        """Carga el último registro del archivo CSV."""
        try:
            if not os.path.exists(self.csv_file):
                self.logger.warning("No existe el archivo de registros")
                return

            if os.path.getsize(self.csv_file) == 0:
                self.logger.info("El archivo de registros está vacío")
                return

            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                registros = list(reader)
                if len(registros) > 1:  # Si hay registros (excluyendo encabezados) 
                    ultimo_registro = registros[-1]
                    self.lbl_ultimo.setText(f"Último Registro: {ultimo_registro[0]} - {ultimo_registro[1]} - {ultimo_registro[3]} - {ultimo_registro[4]} - {ultimo_registro[5]} Kg")
        except Exception as e:
                    
                    # Limpiar y actualizar tabla
                    self.tabla_historial.setRowCount(0)
                    self.tabla_historial.setRowCount(1)
                    self.tabla_historial.setRowCount(3)
                    self.tabla_historial.setRowCount(4)
                    self.tabla_historial.setRowCount(5)
                    for col, valor in enumerate(ultimo_registro):
                        item = QTableWidgetItem(valor)
                        self.tabla_historial.setItem(0, col, item)
        except Exception as e:
            self.logger.error(f"Error al cargar último registro: {str(e)}")

    def guardar_registro(self):
        self.inactivity_timer.start()
        if not self.serial:
            self.logger.warning("Intento de guardar registro sin conexión serial")
            QMessageBox.warning(self, "Desconectado", "Primero debe conectar a un puerto COM")
            return

        operario = self.cmb_operarios.currentText().strip()
        cedula = self.txt_cedula.text().strip()
        producto = self.cmb_productos.currentText().strip()
        nombre_pro = self.txt_nombre_pro.text().strip()
        cantidad = self.txt_cantidad.text().strip()
        peso = self.lbl_peso.text().replace(" Kg", "")

        if not operario or not cedula or not producto or peso == "0.00" or not cantidad or not nombre_pro:
            self.logger.warning("Intento de guardar registro con datos incompletos")
            QMessageBox.warning(self, "Datos incompletos", "Completa todos los campos antes de guardar")
            return
        
        if not cedula.isdigit():
            self.logger.warning(f"Intento de guardar registro con cédula inválida: {cedula}")
            QMessageBox.warning(self, "Cédula invalida", "La cédula deber contener solo números")
            return
        
        if operario in self.operarios_dict and self.operarios_dict[operario]!= cedula:
            self.logger.warning(f"Conflicto de cédula para operario {operario}")
            QMessageBox.warning(self, "Conflicto de cédula", 
                              "La cédula ingresada no coincide con la registrada para este operario")
            return

        if cedula in self.operarios_dict and self.operarios_dict[cedula]!= operario:
            self.logger.warning(f"Conflicto de operario para cédula {cedula}")
            QMessageBox.warning(self, "Conflito", f"La cédula {cedula} ya está registrada con otro operario")
            return
        
        

        fecha_hora = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")

        try:
            with open(self.csv_file, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([fecha_hora, operario, cedula, producto, cantidad, peso])
            
            self.logger.info(f"Registro guardado: {operario} - {producto} - {cantidad} - {peso} Kg")
            
            if operario not in self.operarios_dict:
                self.agregar_operario(operario, cedula)
                self.logger.info(f"Nuevo operario agregado: {operario}")

            if producto not in self.productos_dict:
                self.agregar_producto(producto, nombre_pro)
                self.logger.info(f"Nuevo producto agregado: {producto}")

            # Actualizar último registro
            self.lbl_ultimo.setText(f"Último Registro: {fecha_hora} - {operario} - {producto} - {nombre_pro} - {cantidad} - {peso} Kg")

            # Guardar datos para impresión
            self.ultimo_registro = {
                'operario': operario,
                'cedula': cedula,
                'producto': producto,
                'nombre_pro': nombre_pro,
                'peso': peso,
                'cantidad': cantidad,
                'fecha_hora': fecha_hora
            }

            # Habilitar botón de impresión
            self.btn_imprimir.setEnabled(True)
            
            self.logger.info("Registro guardado correctamente")
            #QMessageBox.information(self, "Guardado", "Registro guardado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al guardar registro: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error al guardar el registro: {str(e)}")

    def abrir_login_admin(self):
        from gui.admin_login import AdminLogin

        # Crear y mostrar el diálogo de login solo si no existe
        if getattr(self, "admin_login_dialog", None) is None:
            self.admin_login_dialog = AdminLogin(self)
            self.admin_login_dialog.setModal(True)
            # Cuando el diálogo termine, manejamos el resultado en _on_admin_login_finished
            self.admin_login_dialog.finished.connect(self._on_admin_login_finished)
            # Al destruirse, reseteamos la referencia
            self.admin_login_dialog.destroyed.connect(self._reset_admin_login)

        # Traer al frente si ya existía
        self.admin_login_dialog.show()
        self.admin_login_dialog.raise_()
        self.admin_login_dialog.activateWindow()
        
    def _on_admin_login_finished(self, result):
        # result == QDialog.Accepted indica que se llamó a accept() en AdminLogin
        if result == QDialog.Accepted:
            self.show_admin_panel()
        # limpiar referencia al finalizar (si el diálogo no se destruye inmediatamente)
        self.admin_login_dialog = None
    
    def show_admin_panel(self):
        from gui.admin_panel import AdminPanel

        # Crear el panel solo si no existe ya una instancia
        if getattr(self, "admin_panel_window", None) is None:
            # AdminPanel no espera parent en su __init__, crear sin argumentos
            self.admin_panel_window = AdminPanel()
            # Al destruirse el panel, reseteamos la referencia
            self.admin_panel_window.destroyed.connect(self._reset_admin_panel)

        # Mostrar y traer al frente
        self.admin_panel_window.show()
        self.admin_panel_window.raise_()
        self.admin_panel_window.activateWindow()

    def _reset_admin_login(self):
        self.admin_login_dialog = None

    def _reset_admin_panel(self):
        self.admin_panel_window = None
        

    def cerrar_programa(self):
        try:
            self.timer.stop()
        except Exception as e:
            self.logger.error(f"Error al detener timer: {str(e)}")
        try:
            self.inactivity_timer.stop()
        except Exception as e:
            self.logger.error(f"Error al detener timer de inactividad: {str(e)}")
        try:
            if self.serial and self.serial.is_open:
                self.serial.close()
                self.logger.info("Puerto serial cerrado")
        except Exception as e:
            self.logger.error(f"Error al cerrar puerto serial: {str(e)}")
        self.logger.info("Aplicación cerrada")
        self.close()

    def abrir_historial(self):
        """Abre la ventana de historial de registros."""
        try:
            self.historial_window = HistorialWindow()
            self.historial_window.show()
        except Exception as e:
            self.logger.error(f"Error al abrir historial: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error al abrir historial: {str(e)}")

    def imprimir_ticket(self):
        """Imprime un ticket con los datos del último registro guardado."""
        if not hasattr(self, 'ultimo_registro'):
            QMessageBox.warning(self, "Error", "No hay registro para imprimir")
            return

        try:
            resultado = self.print_manager.print_ticket(
                self.ultimo_registro['fecha_hora'],
                self.ultimo_registro['operario'],
                self.ultimo_registro['cedula'],
                self.ultimo_registro['producto'],
                self.ultimo_registro['nombre_pro'],
                self.ultimo_registro['cantidad'],
                self.ultimo_registro['peso'],
            )
            if resultado:
                if os.path.exists("configuracion_impresa.pdf"):
                    #print("Ticket impreso correctamente")
                    self.logger.info("Ticket impreso correctamente")
                   # QMessageBox.information(None, "Éxito", "Ticket impreso correctamente")
                return True
            else:
                raise Exception("No se pudo imprimir el ticket")
        except Exception as e:
            self.logger.error(f"Error al imprimir ticket: {str(e)}")
            QMessageBox.critical(self, "Error al imprimir ticket", "Mensaje de error detallado")


    def exportar_backup(self):
        """Exporta una copia de seguridad del archivo CSV de registros."""
        try:
            from datetime import datetime
            import shutil
            
            # Crear nombre del archivo de backup con fecha y hora
            fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_backup = f'backup_registros_{fecha_actual}.csv'
            
            # Permitir al usuario elegir dónde guardar el backup
            from PyQt5.QtWidgets import QFileDialog
            ruta_destino, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar Backup",
                nombre_backup,
                "Archivos CSV (*.csv)"
            )
            
            if ruta_destino:
                # Copiar el archivo de registros al destino seleccionado
                shutil.copy2(self.csv_file, ruta_destino)
                self.logger.info(f"Backup creado exitosamente en: {ruta_destino}")
                QMessageBox.information(
                    self,
                    "Backup Exitoso",
                    f"Se ha creado una copia de seguridad en:\n{ruta_destino}"
                )
        except Exception as e:
            self.logger.error(f"Error al crear backup: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo crear el backup: {str(e)}"
            )
    
    def limpiar_campos(self):
        try:
            # Limpiar los campos de texto
            self.cmb_operarios.setCurrentText("")
            self.txt_cedula.clear()
            self.cmb_productos.setCurrentText("")
            self.txt_nombre_pro.clear()
            self.txt_cantidad.clear()
            self.lbl_peso.setText("0.00 Kg")
            self.txt_cantidad.clear()
            
            self.logger.info("Campos limpiados exitosamente:")
            
        except Exception as e:
            self.logger.error(f"Error al limpiar campos: {str(e)}")
