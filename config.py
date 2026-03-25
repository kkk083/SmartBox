# Configuration SmartBox

# Authentification dashboard
AUTH_USER = 'admin'
AUTH_PASS = '1234'

# Port série Arduino
SERIAL_PORT = '/dev/ttyACM0'
SERIAL_BAUD = 9600

# Fichier de sauvegarde des données
DATA_FILE = 'smartbox_data.json'

# Clé secrète Flask (pour les sessions)
SECRET_KEY = 'smartbox-secret-key-change-me'

# Serveur web
DEBUG = True
HOST = '0.0.0.0'
PORT = 5000

# Configuration email (optionnel)
EMAIL_CONFIG = {
    'enabled': False,
    'address': '',
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'smtp_user': '',      # ton.email@gmail.com
    'smtp_pass': '',      # mot de passe d'application Gmail
    'sender': 'SmartBox <smartbox@noreply.com>'
}
