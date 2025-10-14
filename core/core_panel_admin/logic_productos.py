from core.core_panel_admin.worker.csv_service import CSVService

class LogicProductos:
    @staticmethod
    def cargar_productos(ruta):
        return CSVService.leer_csv(ruta)

    @staticmethod
    def guardar_productos(ruta, datos):
        CSVService.escribir_csv(ruta, datos)