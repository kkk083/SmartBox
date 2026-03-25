# Gestion des codes temporaires

import random
import threading
import time
from datetime import datetime, timedelta
from models import active_code, add_event, save_data
from serial_handler import send_to_arduino

# Limites de durée
MIN_DURATION = 1          # 1 seconde minimum
MAX_DURATION = 86400      # 24 heures maximum

def generate_code(duration_seconds):
    """Génère un nouveau code temporaire"""
    
    # Valide la durée
    duration_seconds = max(MIN_DURATION, min(MAX_DURATION, duration_seconds))
    
    # Génère un code 4 chiffres
    code = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    
    # Calcule l'expiration
    expires_at = datetime.now() + timedelta(seconds=duration_seconds)
    
    # Stocke le code
    active_code['code'] = code
    active_code['expires_at'] = expires_at.strftime('%Y-%m-%d %H:%M:%S')
    active_code['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Envoie à l'Arduino
    send_to_arduino(f"CODE:{code}")
    
    # Log l'événement
    duration_str = format_duration(duration_seconds)
    add_event(f"Code {code} généré ({duration_str})", "code")
    
    save_data()
    return code

def revoke_code():
    """Révoque le code actif"""
    
    if active_code['code']:
        old_code = active_code['code']
        active_code['code'] = None
        active_code['expires_at'] = None
        active_code['created_at'] = None
        
        # Envoie à l'Arduino
        send_to_arduino("REVOKE")
        
        add_event(f"Code {old_code} révoqué", "code")
        save_data()
        return True
    return False

def is_code_active():
    """Vérifie si un code est actif et non expiré"""
    
    if not active_code['code'] or not active_code['expires_at']:
        return False
    
    expires_at = datetime.strptime(active_code['expires_at'], '%Y-%m-%d %H:%M:%S')
    return datetime.now() < expires_at

def check_code_expiration():
    """Thread qui vérifie l'expiration du code"""
    
    while True:
        if active_code['code'] and active_code['expires_at']:
            expires_at = datetime.strptime(active_code['expires_at'], '%Y-%m-%d %H:%M:%S')
            
            if datetime.now() >= expires_at:
                old_code = active_code['code']
                active_code['code'] = None
                active_code['expires_at'] = None
                active_code['created_at'] = None
                
                send_to_arduino("REVOKE")
                add_event(f"Code {old_code} expiré", "code")
                save_data()
        
        time.sleep(1)

def format_duration(seconds):
    """Formate une durée en texte lisible"""
    
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        if secs:
            return f"{minutes}min {secs}s"
        return f"{minutes}min"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes:
            return f"{hours}h {minutes}min"
        return f"{hours}h"
