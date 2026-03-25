# Modèles de données SmartBox

import json
import os
from datetime import datetime
from config import DATA_FILE, EMAIL_CONFIG

# État de la boîte aux lettres
box_status = {
    'door_open': False,
    'door_locked': True,
    'mail_present': False,
    'parcel_present': False,
    'arduino_connected': False
}

# Code actif
active_code = {
    'code': None,
    'expires_at': None,
    'created_at': None
}

# Historique des événements
events_log = []

# Configuration email (copie modifiable)
email_config = EMAIL_CONFIG.copy()

def add_event(description, event_type='system'):
    """Ajoute un événement à l'historique"""
    event = {
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'description': description,
        'type': event_type
    }
    events_log.insert(0, event)
    
    # Garde seulement les 50 derniers événements
    if len(events_log) > 50:
        events_log.pop()
    
    save_data()
    return event

def save_data():
    """Sauvegarde les données dans un fichier JSON"""
    data = {
        'box_status': box_status,
        'active_code': active_code,
        'events_log': events_log,
        'email_config': {
            'enabled': email_config.get('enabled', False),
            'address': email_config.get('address', '')
        }
    }
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Erreur sauvegarde: {e}")

def load_data():
    """Charge les données depuis le fichier JSON"""
    global box_status, active_code, events_log, email_config
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            
            # Charge l'historique
            if 'events_log' in data:
                events_log.clear()
                events_log.extend(data['events_log'])
            
            # Charge la config email
            if 'email_config' in data:
                email_config['enabled'] = data['email_config'].get('enabled', False)
                email_config['address'] = data['email_config'].get('address', '')
            
            # Charge l'état de la boîte (NOUVEAU)
            if 'box_status' in data:
                saved = data['box_status']
                box_status['mail_present'] = saved.get('mail_present', False)
                box_status['parcel_present'] = saved.get('parcel_present', False)
            
            print(f"Données chargées depuis {DATA_FILE}")
        except Exception as e:
            print(f"Erreur chargement: {e}")
