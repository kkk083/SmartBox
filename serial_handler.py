# Communication série avec Arduino

import serial
import time
from config import SERIAL_PORT, SERIAL_BAUD
from models import box_status, active_code, add_event
from email_handler import send_email_notification
from push_handler import send_push_notification

# Connexion série
ser = None

def init_serial():
    """Initialise la connexion série avec l'Arduino"""
    global ser
    
    try:
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
        time.sleep(2)
        box_status['arduino_connected'] = True
        print(f"Arduino connecté sur {SERIAL_PORT}")
        add_event("Arduino connecté", "system")
        return True
    except Exception as e:
        print(f"Arduino non connecté: {e}")
        print("Le dashboard fonctionne quand même (mode démo).")
        box_status['arduino_connected'] = False
        return False

def send_to_arduino(message):
    """Envoie un message à l'Arduino"""
    global ser
    
    if ser and ser.is_open:
        try:
            ser.write(f"{message}\n".encode())
            print(f"[ENVOYÉ] {message}")
            return True
        except Exception as e:
            print(f"[ERREUR ENVOI] {e}")
            return False
    else:
        print(f"[SIMULÉ] {message}")
        return False

def listen_arduino():
    """Thread d'écoute des messages Arduino"""
    global ser
    
    while True:
        if ser and ser.is_open:
            try:
                if ser.in_waiting > 0:
                    message = ser.readline().decode().strip()
                    if message:
                        handle_arduino_message(message)
            except Exception as e:
                print(f"[ERREUR LECTURE] {e}")
                box_status['arduino_connected'] = False
        time.sleep(0.1)

def handle_arduino_message(message):
    """Traite les messages reçus de l'Arduino"""
    print(f"[REÇU] {message}")
    
    if message == "SMARTBOX_READY":
        box_status['arduino_connected'] = True
        add_event("SmartBox prête", "system")
        if active_code['code']:
            send_to_arduino(f"CODE:{active_code['code']}")
    
    elif message == "MAIL_DETECTED":
        box_status['mail_present'] = True
        add_event("Courrier détecté", "mail")
        send_email_notification(
            "Courrier reçu !",
            "Vous avez reçu du courrier dans votre SmartBox."
        )
        send_push_notification(
            "📬 Courrier reçu !",
            "Du courrier est arrivé dans votre SmartBox."
        )
    
    elif message == "MAIL_CLEARED":
        box_status['mail_present'] = False
        add_event("Courrier récupéré", "mail")
    
    elif message == "CODE_OK":
        add_event("Code accepté - Accès autorisé", "access_granted")
        send_email_notification(
            "Accès autorisé",
            "Le code d'accès a été utilisé. La porte est déverrouillée."
        )
        send_push_notification(
            "✅ Accès autorisé",
            "Le livreur a ouvert votre SmartBox."
        )
    
    elif message == "CODE_FAIL":
        add_event("Tentative de code invalide", "access_denied")
        send_email_notification(
            "Tentative d'accès échouée",
            "Quelqu'un a essayé un code invalide sur votre SmartBox."
        )
        send_push_notification(
            "⚠️ Tentative suspecte",
            "Quelqu'un a tapé un mauvais code sur votre SmartBox."
        )
    
    elif message == "DOOR_OPENED":
        box_status['door_open'] = True
        box_status['door_locked'] = False
        add_event("Porte ouverte", "door")
    
    elif message == "DOOR_CLOSED":
        box_status['door_open'] = False
        box_status['door_locked'] = True
        add_event("Porte fermée et verrouillée", "door")
    
    elif message == "PARCEL_DETECTED":
        box_status['parcel_present'] = True
        add_event("Colis déposé", "parcel")
        send_email_notification(
            "Colis livré !",
            "Un colis a été déposé dans votre SmartBox."
        )
        send_push_notification(
            "📦 Colis livré !",
            "Un colis a été déposé dans votre SmartBox."
        )
    
    elif message == "PARCEL_NONE":
        if box_status['parcel_present']:
            add_event("Colis récupéré", "parcel")
            send_email_notification(
                "Colis récupéré",
                "Le colis a été retiré de votre SmartBox."
            )
            send_push_notification(
                "✅ Colis récupéré",
                "Le colis a été retiré de votre SmartBox."
            )
        box_status['parcel_present'] = False
    
    elif message == "CODE_RECEIVED":
        add_event("Code envoyé à la boîte", "code")
    
    elif message == "CODE_REVOKED":
        add_event("Code révoqué sur la boîte", "code")