from core.core_panel_admin.worker.csv_service import CSVService

class LogicOperarios:
    @staticmethod
    def validar_cedulas_unicas(datos):
        cedulas = set()
        for _, cedula in datos:
            if not cedula.isdigit():
                raise ValueError(f"La cédula '{cedula}' debe contener solo números.")
            if cedula in cedulas:
                raise ValueError(f"La cédula '{cedula}' está duplicada.")
            cedulas.add(cedula)

    @staticmethod
    def cargar_operarios(ruta):
        return CSVService.leer_csv(ruta)

    @staticmethod
    def guardar_operarios(ruta, datos):
        CSVService.escribir_csv(ruta, datos)
