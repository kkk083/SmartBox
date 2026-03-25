#!/usr/bin/env python3
"""
SMARTBOX - Boîte aux Lettres Connectée
Dashboard Flask + Communication Arduino
"""

import threading
from flask import Flask
from config import SECRET_KEY, DEBUG, HOST, PORT
from models import load_data
from serial_handler import init_serial, listen_arduino
from code_manager import check_code_expiration
from push_handler import init_vapid
from routes import api

# Crée l'application Flask
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Enregistre les routes
app.register_blueprint(api)

def main():
    """Point d'entrée principal"""
    
    print("=" * 50)
    print("  SMARTBOX - Boite aux Lettres Connectee v2.0")
    print("=" * 50)
    
    # Charge les données sauvegardées
    load_data()
    
    # Initialise les clés VAPID pour les notifications push
    init_vapid()
    
    # Initialise la connexion série
    init_serial()
    
    # Lance le thread d'écoute Arduino
    serial_thread = threading.Thread(target=listen_arduino, daemon=True)
    serial_thread.start()
    
    # Lance le thread de vérification d'expiration des codes
    expiration_thread = threading.Thread(target=check_code_expiration, daemon=True)
    expiration_thread.start()
    
    print()
    print(f"  Dashboard : http://{HOST}:{PORT}")
    print(f"  Login : admin / 1234")
    print()
    
    # Lance le serveur Flask
    app.run(host=HOST, port=PORT, debug=DEBUG, use_reloader=False)

if __name__ == '__main__':
    main()