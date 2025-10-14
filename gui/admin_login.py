from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from gui.admin_panel import AdminPanel

class AdminLogin(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        print("Ventana de login iniciada")
        self.setWindowTitle("Modo Administrador - Ingreso")
        self.setMinimumSize(300, 150)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.label = QLabel("Ingrese la contraseña:")
        layout.addWidget(self.label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("Entrar")
        self.login_button.clicked.connect(self.verificar_password)
        layout.addWidget(self.login_button)

        self.setLayout(layout)
        
    def verificar_password(self):
        from core.login.admin_login_services import AdminLoginService  # import perezoso para evitar circularidad
        password = self.password_input.text()
        service = AdminLoginService()
        if service.verificar_password(password):
            self.accept()
        else:
            QMessageBox.warning(self, "Acceso denegado", "Contraseña incorrecta.")

    def abrir_panel_admin(self):
        self.panel = AdminPanel()
        self.panel.exec_()

