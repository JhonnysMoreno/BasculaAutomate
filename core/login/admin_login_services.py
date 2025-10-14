from PyQt5.QtWidgets import *

from gui.admin_panel import AdminPanel  # Importamos la siguiente ventana si se autentica correctamente
#from services.user_repository import UserRepository
from gui.admin_login import AdminLogin

class AdminLoginService:
    def __init__(self, user_repo=None):
        # user_repo puede ser una capa de datos si la agregas luego
        self.user_repo = user_repo

    def verificar_password(self, password: str) -> bool:
        """
        Verifica la contraseña del administrador.
        """
        # Implementación temporal: contraseña dura
        return password == "BasculaKP2025*"

        
    password_input = AdminLogin().password_input
