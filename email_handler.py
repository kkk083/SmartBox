# Gestion des emails SmartBox

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models import email_config, add_event

def send_email_notification(subject, body):
    """Envoie une notification par email"""
    
    # Vérifie si les emails sont activés
    if not email_config.get('enabled') or not email_config.get('address'):
        return False
    
    # Si SMTP pas configuré, simule l'envoi
    if not email_config.get('smtp_user') or not email_config.get('smtp_pass'):
        print(f"[EMAIL SIMULÉ] {subject}: {body}")
        add_event(f"Email simulé: {subject}", "email")
        return True
    
    try:
        # Crée le message
        msg = MIMEMultipart()
        msg['Subject'] = f"[SmartBox] {subject}"
        msg['From'] = email_config.get('sender', 'SmartBox')
        msg['To'] = email_config['address']
        msg.attach(MIMEText(body, 'plain'))
        
        # Connexion SMTP
        with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
            server.starttls()
            server.login(email_config['smtp_user'], email_config['smtp_pass'])
            server.send_message(msg)
        
        print(f"[EMAIL ENVOYÉ] {subject} -> {email_config['address']}")
        add_event(f"Email envoyé: {subject}", "email")
        return True
        
    except Exception as e:
        print(f"[EMAIL ERREUR] {e}")
        add_event(f"Erreur email: {str(e)}", "system")
        return False
