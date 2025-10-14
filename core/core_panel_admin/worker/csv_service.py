import csv, os

class CSVService:
    @staticmethod
    def ensure_csv_exists(ruta, headers):
        """Crea el CSV si no existe."""
        if not os.path.exists(ruta):
            with open(ruta, mode='w', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow(headers)

    @staticmethod
    def leer_csv(ruta):
        """Devuelve una lista con los registros del CSV."""
        with open(ruta, newline='', encoding='utf-8') as f:
            return list(csv.reader(f))

    @staticmethod
    def escribir_csv(ruta, datos):
        """Guarda los datos en un archivo CSV."""
        with open(ruta, mode='w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerows(datos)
