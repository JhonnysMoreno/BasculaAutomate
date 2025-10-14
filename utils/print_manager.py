import win32print
import win32api
import win32ui
import win32con
from datetime import datetime
import os
from tkinter import filedialog, messagebox
from PyQt5.QtWidgets import *
import tkinter as tk
import time
import json
import os
import math
import pywintypes
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from utils.logger_config import setup_logger

class PrintManager:
    """
    Clase para manejar la impresión de tickets.
    """
    _root = None  # Variable de clase para la ventana de Tkinter
    
    def __init__(self, printer_name=None):
        self.logger = setup_logger()
        self.printer_name = printer_name or self.get_default_printer()
        self._init_tkinter()
        
    @classmethod
    def _init_tkinter(cls):
        """Inicializa la ventana de Tkinter una sola vez para todas las instancias."""
        if cls._root is None:
            cls._root = tk.Tk()
            cls._root.withdraw()
        
    def get_default_printer(self):
        """Obtiene la impresora predeterminada del sistema."""
        try:
            # Intenta obtener la impresora predeterminada
            printer = win32print.GetDefaultPrinter()
            return printer
        except pywintypes.error as e:
            # Si no hay impresora predeterminada, obtén la lista de impresoras
            printers = [printer[2] for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)]
            if not printers:
                self.logger.error("No hay impresoras instaladas en el sistema")
                QMessageBox.critical(None, "Error", "No hay impresoras instaladas en el sistema")
                return None
            # Usa la primera impresora disponible
            self.logger.info(f"Usando primera impresora disponible: {printers[0]}")
            return printers[0]
        except pywintypes.error as e:
            self.logger.error(f"Error al obtener impresora predeterminada: {e}")
          #  print(f"Error al obtener impresora predeterminada: {e}")
            QMessageBox.critical("Error", f"Error al obtener impresora predeterminada: {e}")
            return None

    def load_config(self):
        config_path = "printer_config.json"
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.logger.info(f"Cargando configuración desde: {config_path}")
                    return json.load(f)
            self.logger.error(f"No se encontró el archivo de configuración en: {config_path}")
            raise FileNotFoundError(f"No se encontró el archivo de configuración en: {config_path}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Error en el formato del archivo JSON: {e}")
          #  print(f"Error en el formato del archivo JSON: {e}")
            QMessageBox.critical(None, "Error", f"Error en el formato del archivo de configuración: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Error inesperado al cargar la configuración: {e}")
          #  print(f"Error inesperado al cargar la configuración: {e}")
            QMessageBox.critical("Error", f"Error inesperado al cargar la configuración: {e}")
            return {}
    
    def validar_config_json(self, config_path):
        try:
            if not isinstance(config_path, dict):
                raise ValueError("La configuración debe ser un diccionario")
                
            # Validar claves principales
            if "printer" not in config_path:
                raise ValueError("El JSON no contiene una impresora configurada")
            if not config_path["printer"]:
                raise ValueError("El nombre de la impresora no puede estar vacío")
                
            # Validar dimensiones
            for dim in ["Alto_Hoja", "Ancho_Hoja"]:
                if dim not in config_path:
                    raise ValueError(f"Falta la dimensión '{dim}' en el JSON")
                if not isinstance(config_path[dim], (int, float)) or config_path[dim] <= 0:
                    raise ValueError(f"'{dim}' debe ser un número positivo")
            
            # Validar tipo de tamaño de hoja
            if not isinstance(config_path["Alto_Hoja"], (int, float)):
                raise TypeError("'Alto_Hoja' debe ser numérico.")
            if not isinstance(config_path["Ancho_Hoja"], (int, float)):
                raise TypeError("'Ancho_Hoja' debe ser numérico.")

            # Lista de campos obligatorios
            campos_obligatorios = ["operario", "cantidad", "codigo_producto", "nombre_producto", "peso", "fecha"]
            
            for campo in campos_obligatorios:
                if campo not in config_path["campos"]:
                    raise ValueError(f"Falta el campo '{campo}' en la configuración.")
                if not isinstance(config_path["campos"][campo], dict):
                    raise TypeError(f"'{campo}' debe ser un diccionario con claves 'x' e 'y'.")
                if "x" not in config_path["campos"][campo] or "y" not in config_path["campos"][campo]:
                    raise ValueError(f"El campo '{campo}' debe tener claves 'x' e 'y'.")
                if not isinstance(config_path["campos"][campo]["x"], (int, float)) or not isinstance(config_path["campos"][campo]["y"], (int, float)):
                    raise TypeError(f"Las posiciones de '{campo}' deben ser valores numéricos.")

            return True  # Todo bien

        except Exception as e:
            print(f"Error de validación del JSON: {e}")
            raise  # Relanza para que el try del PDF lo capture si hace falta


    def is_tsc_printer(self):
        try:
            tsc_models = [
                'TSC TTP', 'TSC TDP', 'TSC TE', 'TSC TX', 'TSC', 
                'TSC 241', 'TSC-241', 'TTP-247', 'TTP-345', 
                'TDP-247', 'TDP-345', 'TSC TTP-247', 'TSC TTP-345'
            ]
            printer_name = self.printer_name.upper()
            #print(f"Verificando impresora: {printer_name}")
            self.logger.info(f"Verificando si {printer_name} es una impresora TSC")
            return any(model.upper() in printer_name for model in tsc_models)
        except Exception as e:
            print(f"Error al verificar impresora TSC: {e}")
            self.logger.error(f"Error al verificar impresora TSC: {e}")
            QMessageBox.critical(None, "Error", f"Error al verificar impresora TSC: {e}")
            return False

    def check_printer_status(self):
        
        try:
            hPrinter = win32print.OpenPrinter(self.printer_name)
            printer_info = win32print.GetPrinter(hPrinter, 2)
            status = printer_info.get('pStatus', 0)
            self.logger.info(f"Verificando estado de la impresora: {self.printer_name}")
            
            # Códigos de estado comunes
            status_messages = {
                0: "Lista",
                1: "Pausada",
                2: "Error",
                3: "Pendiente de eliminación",
                4: "Papel agotado",
                5: "Papel atascado",
                6: "Necesita atención del usuario",
                7: "Procesando",
                8: "Inicializando",
                9: "En espera de impresión",
                10: "Imprimiendo",
                11: "Fuera de línea",
                12: "Apagada"
            }
            
            win32print.ClosePrinter(hPrinter)
            
            if status == 0:
                return (True, "La impresora está lista")  # Retorna una tupla
            else:
                mensaje = f"Estado de la impresora: {status_messages.get(status, 'Estado desconocido')}"
                return (False, mensaje)  # Retorna una tupla
                
        except pywintypes.error as e:
            return (False, f"Error al abrir la impresora: {e}")  # Retorna una tupla
        except Exception as e:
            return (False, f"Error al verificar el estado de la impresora: {str(e)}")  # Retorna una tupla
    
    def validate_printer_connection(self):
        try:
            # Verificar si hay una impresora configurada
            if not self.printer_name:
                self.logger.info("Validando conexión con la impresora")
                return (False, "No hay una impresora configurada")

            # Obtener lista de impresoras instaladas
            impresoras_instaladas = [printer[2] for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)]
            
            # Verificar si la impresora está instalada
            if self.printer_name not in impresoras_instaladas:
                return (False, f"La impresora '{self.printer_name}' no está instalada en el sistema")

            # Verificar el estado de la impresora
            printer_ready, status_message = self.check_printer_status()
            if not printer_ready:
                return (False, f"La impresora no está lista: {status_message}")

            return (True, "La impresora está conectada y lista para usar")

        except pywintypes.error as e:
            return (False, f"Error al validar la conexión con la impresora: {e}")
        except Exception as e:
            return (False, f"Error inesperado al validar la impresora: {str(e)}")
        
        
    @staticmethod
    def tsc_dots_to_pdf_points(dots, dpi=203):
        """
        Convierte puntos TSC a puntos PDF
        Args:
            dots: número de puntos TSC
            dpi: resolución de la impresora (por defecto 203 DPI para TSC)
        Returns:
            float: puntos PDF equivalentes
        """
        return float(dots) * (72.0 / dpi)


    def print_ticket(self, fecha_hora, operario, cedula, producto, nombre_pro, cantidad, peso):
        try:
            # Cargar configuración
            config_path = self.load_config()
            self.validar_config_json(config_path)
            
            # Actualizar la impresora con la configurada en el JSON
            self.printer_name = config_path.get("printer", self.printer_name)
            
            # Validar la conexión con la impresora primero
            printer_connected, connection_message = self.validate_printer_connection()
            if not printer_connected:
                #print(f"Error de conexión con la impresora: {connection_message}")
                self.logger.info(f"Error de conexión con la impresora: {connection_message}")
                QMessageBox.critical(None, "Error", f"Error de conexión con la impresora:\n{connection_message}")
                return False

            campos = config_path["campos"]

            # Primero definir las dimensiones de la hoja
            alto_hoja = int(config_path["Alto_Hoja"]) * 2.83465
            ancho_hoja = int(config_path["Ancho_Hoja"]) * 2.83465

            # Crear el PDF con el tamaño correcto desde el inicio
            pdf_path = "configuracion_impresa.pdf"
            ticket_content = canvas.Canvas(pdf_path, pagesize=(ancho_hoja, alto_hoja))

            # Verificar estado de la impresora
            printer_ready, status_message = self.check_printer_status()
            if not printer_ready:
                print(f"Error: {status_message}")
                return False

            # Dibujar los textos en sus posiciones
            # Obtener el tamaño de fuente general desde la configuración
            size_general = config_path.get("SizeG_Fuentes", 10)  # Si no existe, usa 10 como valor predeterminado

            # Dictionary mapping field names to their labels
            field_labels = {
                "titulo": "",  # El título no necesita etiqueta
                "fecha": "Fecha",
                "operario": "Operario",
                "codigo_producto": "Código Producto",
                "nombre_producto": "Nombre Producto",
                "cantidad": "Cantidad", 
                "peso": "Peso"
            }

            # Dictionary mapping field names to their values
            field_values = {
                "titulo": config_path.get("Titulo"),
                "fecha": fecha_hora,
                "operario": operario,
                "codigo_producto": producto,
                "nombre_producto": nombre_pro,  
                "cantidad": cantidad, 
                "peso": f"{peso} Kg"
            }

            # Draw all fields in a single loop
            for field_name, label in field_labels.items():
                x = campos[field_name]["x"]
                y = alto_hoja - campos[field_name]["y"]
                
                x_PDF = self.tsc_dots_to_pdf_points(x)
                y_PDF = self.tsc_dots_to_pdf_points(y)
                
                
                # Invertir la coordenada Y restándola de la altura total
                value = field_values[field_name]
                if field_name == "titulo":
                    ticket_content.setFont("Helvetica-Bold", 14)
                    ticket_content.drawString(x_PDF, y_PDF, value)
                    ticket_content.setFont("Helvetica", size_general)
                else:
                    ticket_content.drawString(x_PDF, y_PDF, f"{label}: {value}")

            # Guardar el contenido del PDF
            ticket_content.save()

            # Manejar diferentes tipos de impresoras
            if "Microsoft Print to PDF" in self.printer_name:
                result = self._print_to_pdf(ticket_content)
                if result is None:  # Si fue cancelado
                    if os.path.exists("configuracion_impresa.pdf"):
                        os.remove("configuracion_impresa.pdf")
                    return True  # Retornamos True sin mostrar mensaje
                return result
            elif self.is_tsc_printer():
                # Verificar si es una impresora TSC
                if any(tsc_model in self.printer_name.upper() for tsc_model in ["TSC"]):
                   # print("Detectada impresora TSC, usando modo optimizado")
                    self.logger.info("Detectada impresora TSC, usando modo optimizado")
                    return self._print_tsc(ticket_content, fecha_hora, operario, cedula, 
                                     producto, nombre_pro, cantidad, peso)
                
                else:
                    return self._print_standard(ticket_content)

        except Exception as e:
            # Solo mostrar mensaje de error si no fue una cancelación
            if str(e) != "cancelled":
               # print(f"Error al generar el PDF: {e}")
                self.logger.info(f"Error al generar el PDF: {e}")
                QMessageBox.critical(None, "Error", f"No se pudo generar el archivo PDF:\n{e}")
            if os.path.exists("configuracion_impresa.pdf"):
                os.remove("configuracion_impresa.pdf")
            return False

    def _print_to_pdf(self, ticket_content):
        """Maneja la impresión a PDF."""
        try:
            
            # Crear nombre de archivo por defecto
            default_filename = f"ticket_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            self.logger.info("Iniciando impresión a PDF")
            
            # Mostrar diálogo para guardar
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                initialfile=default_filename,
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialdir=os.path.expanduser("~\\Documents")
            )
            
            if not file_path:  # Si el usuario cancela
                # Eliminar el archivo temporal si existe
                if os.path.exists("configuracion_impresa.pdf"):
                    os.remove("configuracion_impresa.pdf")
                return None  # Retornamos None para indicar que fue cancelado
            
            # Convertir la ruta a formato de Windows
            file_path = os.path.normpath(file_path)
            
            # Copiar el archivo temporal al destino seleccionado usando shutil
            try:
                import shutil
                if os.path.exists("configuracion_impresa.pdf"):
                    shutil.copy2("configuracion_impresa.pdf", file_path)
                    # Eliminar el archivo temporal después de copiarlo
                    os.remove("configuracion_impresa.pdf")
                    return True
                else:
                 #   print("No se encontró el archivo PDF temporal")
                    self.logger.info("No se encontró el archivo PDF temporal")
                    return False
            except Exception as e:
             #   print(f"Error al copiar el archivo PDF: {e}")
                self.logger.error(f"Error al copiar el archivo PDF: {e}")
                return False
                
        except Exception as e:
          #  print(f"Error al imprimir a PDF: {str(e)}")
            self.logger.error(f"Error al imprimir a PDF: {str(e)}") 
            return False
        

    def _print_tsc(self, ticket_content, fecha_hora, operario, cedula, producto, nombre_pro, cantidad, peso):
        """
        Maneja la impresión específica para impresoras TSC.
        """
        hprinter = None
        try:
            config = self.load_config()
            self.logger.info("Iniciando impresión para impresora TSC")
            
            # Convertir dimensiones de hoja de mm a dots (203 DPI para TSC)
            dpi = 203  # Resolución estándar TSC
            alto_mm = float(config.get("Alto_Hoja", 80))
            ancho_mm = float(config.get("Ancho_Hoja", 100))
            
            # Convertir mm a dots para el tamaño de la etiqueta
            alto_dots = int(alto_mm * dpi / 25.4)
            ancho_dots = int(ancho_mm * dpi / 25.4)
            
            size_general = config.get("SizeG_Fuentes", 10)
            size_titulo = (size_general / 8)
            size_normal = (size_general / 10)
            
        #    print("=== Configuración de impresión TSC ===")
        #    print(f"Impresora: {self.printer_name}")
        #    print(f"Tamaño etiqueta: {ancho_dots}x{alto_dots} dots")
        #    print("=====================================")
            
            hprinter = win32print.OpenPrinter(self.printer_name)
            docinfo = ('Ticket de Báscula', None, 'RAW')
            job = win32print.StartDocPrinter(hprinter, 1, docinfo)
            
            if job <= 0:
                self.logger.error("No se pudo iniciar el trabajo de impresión")
                raise Exception("No se pudo iniciar el trabajo de impresión")
                
            
            win32print.StartPagePrinter(hprinter)
            
            # Comandos de inicialización corregidos
            setup_commands = [
                "CLS\n",
                f"SIZE {ancho_mm:.1f} mm, {alto_mm:.1f} mm",
                "GAP 3 mm, 0",
                "DIRECTION 1",  # Cambiado de 0 a 1 para corregir la orientación
                "REFERENCE 0,0",
                "OFFSET 0 mm",
                "SET TEAR ON",
                "CODEPAGE 850",
                "DENSITY 8",
                "SPEED 4",
                "BAR 50,55,798,2"
            ]
            
            for command in setup_commands:
                #print(f"Enviando: {command}")
                win32print.WritePrinter(hprinter, f"{command}\n".encode('cp850'))
            
            # Valores de los campos con tamaño de fuente ajustado
            field_values = {
                "titulo": {"text": config.get("Titulo", ""), "size": str(size_titulo)},  # Tamaño más grande para el título
                "fecha": {"text": f"Fecha: {fecha_hora}", "size": str(size_normal)},
                "operario": {"text": f"Operario: {operario}", "size": str(size_normal)},
                "codigo_producto": {"text": f"Codigo: {producto}", "size": str(size_normal)},
                "nombre_producto": {"text": f"Producto: {nombre_pro}", "size": str(size_normal)},
                "cantidad": {"text": f"Cantidad: {cantidad}", "size": str(size_normal)},
                "peso": {"text": f"Peso: {peso} Kg", "size": str(size_normal)}
            }
            
    
            #print("\n=== Comandos de texto ===")
            for field_name, value in field_values.items():
                if field_name in config["campos"]:
                    # Usar coordenadas directamente en píxeles del JSON
                    x = config["campos"][field_name]["x"]
                    y = config["campos"][field_name]["y"]
                    
                    text = value["text"].replace('"', '\\"')
                    size = value["size"]
                    
                    if field_name == "titulo":
                        text_command = f'TEXT {x},{y},"4",0,{size},{size},"{text}"\n'
                    else:
                        text_command = f'TEXT {x},{y},"3",0,{size},{size},"{text}"\n'
                   
                    #print(f"Enviando: {text_command}")
                   # win32print.WritePrinter(hprinter, "BAR 10,310,380,2\n".encode('cp850'))
                    win32print.WritePrinter(hprinter, text_command.encode('cp850'))
            
            # print("Enviando: PRINT 1,1")
            win32print.WritePrinter(hprinter, "PRINT 1,1\n".encode('cp850'))
            
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
            win32print.ClosePrinter(hprinter)
            
            self.logger.info("Impresión completada en la impresora TSC")
            return True
            
        except Exception as e:
            print(f"Error durante la impresión TSC: {str(e)}")
            if hprinter:
                try:
                    win32print.EndDocPrinter(hprinter)
                    win32print.ClosePrinter(hprinter)
                except Exception as close_error:
                    print(f"Error al cerrar la impresora: {close_error}")
            QMessageBox.critical(None, "Error de Impresión TSC", f"Error al imprimir: {str(e)}")
            return False

    def _print_standard(self, ticket_content):
        """Maneja la impresión en impresoras estándar."""
        try:
            hPrinter = win32print.OpenPrinter(self.printer_name)
            self.logger.info("Iniciando impresión para impresora estándar")
            
            # Obtener información de la impresora
            printer_info = win32print.GetPrinter(hPrinter, 2)
            # print(f"Información de la impresora: {printer_info}")
            self.logger.info(f"Información de la impresora: {printer_info}")
            
            print("Iniciando documento...")
            # Intentar diferentes formatos
            formats = [("RAW", "Ticket"), ("XPS_PASS", "Ticket")]
            
            for format_type, doc_name in formats:
                try:
                    doc_info = (doc_name, None, format_type)
                    job_id = win32print.StartDocPrinter(hPrinter, 1, doc_info)
                    # print(f"ID del trabajo de impresión ({format_type}): {job_id}")
                    self.logger.info(f"ID del trabajo de impresión ({format_type}): {job_id}")
                    
                    try:
                        # print("Iniciando página...")
                        win32print.StartPagePrinter(hPrinter)
                        
                        # print("Enviando contenido a la impresora...")
                        formatted_content = ticket_content.encode('utf-8')
                        bytes_written = win32print.WritePrinter(hPrinter, formatted_content)
                        #print(f"Bytes escritos: {bytes_written}")
                        self.logger.info(f"Bytes escritos: {bytes_written}")
                        
                        #print("Finalizando página...")
                        win32print.EndPagePrinter(hPrinter)
                        
                        # Configurar el trabajo para que no se elimine automáticamente
                        #print("Configurando trabajo de impresión...")
                        win32print.SetJob(hPrinter, job_id, 0, None, win32print.JOB_CONTROL_PAUSE)
                        
                        # Esperar un momento para asegurar que el trabajo se registre
                        time.sleep(2)
                        
                        # Reanudar el trabajo
                        print("Reanudando trabajo de impresión...")
                        print("Finalizando documento...")
                        win32print.EndDocPrinter(hPrinter)
                        win32print.ClosePrinter(hPrinter)
                        
                        # Solo mostrar el mensaje si realmente se imprimió
                        if os.path.exists("configuracion_impresa.pdf"):
                            print("Ticket impreso correctamente en la impresora estándar")
                            self.logger.info("Ticket impreso correctamente")
                        return True
                        
                    except Exception as e:
                        #print(f"Error durante la impresión con formato {format_type}: {str(e)}")
                        self.logger.error(f"Error durante la impresión con formato {format_type}: {str(e)}")
                        win32print.AbortPrinter(hPrinter)
                        continue
                        
                except Exception as e:
                    print(f"Error al iniciar documento con formato {format_type}: {str(e)}")
                    self.logger.error(f"Error al iniciar documento con formato {format_type}: {str(e)}")
                    continue
            
            #print("No se pudo imprimir con ningún formato")
            self.logger.error("No se pudo imprimir con ningún formato")
            return False
            
        except Exception as e:
            print(f"Error específico de impresión estándar: {str(e)}")
            self.logger.error(f"Error específico de impresión estándar: {str(e)}")
            return False

