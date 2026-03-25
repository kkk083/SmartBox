# Routes API Flask

import re
from functools import wraps
from flask import Blueprint, request, jsonify, render_template, session, send_from_directory
from config import AUTH_USER, AUTH_PASS
from models import box_status, active_code, events_log, email_config, add_event, save_data
from code_manager import generate_code, revoke_code, is_code_active
from push_handler import save_subscription, VAPID_PUBLIC_KEY

# Crée le Blueprint
api = Blueprint('api', __name__)

# Décorateur pour vérifier l'authentification
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'error': 'Non autorisé'}), 401
        return f(*args, **kwargs)
    return decorated

# ==================== PAGES ====================

@api.route('/')
def index():
    """Page principale (dashboard)"""
    return render_template('dashboard.html')

@api.route('/manifest.json')
def manifest():
    """Sert le manifest PWA"""
    return send_from_directory('static', 'manifest.json')

@api.route('/sw.js')
def sw():
    """Sert le service worker"""
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

# ==================== AUTH ====================

@api.route('/api/login', methods=['POST'])
def api_login():
    """Connexion utilisateur"""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    if username == AUTH_USER and password == AUTH_PASS:
        session['logged_in'] = True
        add_event("Connexion au dashboard", "system")
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Identifiants incorrects'})

@api.route('/api/logout', methods=['POST'])
def api_logout():
    """Déconnexion utilisateur"""
    session.pop('logged_in', None)
    return jsonify({'success': True})

# ==================== STATUS ====================

@api.route('/api/status')
@login_required
def api_status():
    """Retourne l'état complet du système"""
    return jsonify({
        'box': box_status,
        'active_code': {
            'code': active_code['code'],
            'expires_at': active_code['expires_at'],
            'is_active': is_code_active()
        } if active_code['code'] else None,
        'events': events_log[:20],
        'email': {
            'enabled': email_config.get('enabled', False),
            'address': email_config.get('address', '')
        }
    })

# ==================== CODES ====================

@api.route('/api/generate-code', methods=['POST'])
@login_required
def api_generate_code():
    """Génère un nouveau code temporaire"""
    data = request.get_json()
    duration_seconds = data.get('duration_seconds', 3600)
    
    try:
        duration_seconds = int(duration_seconds)
        if duration_seconds < 1:
            return jsonify({'success': False, 'error': 'Durée minimum: 1 seconde'})
        if duration_seconds > 86400:
            return jsonify({'success': False, 'error': 'Durée maximum: 24 heures'})
    except:
        return jsonify({'success': False, 'error': 'Durée invalide'})
    
    code = generate_code(duration_seconds)
    
    return jsonify({
        'success': True,
        'code': code,
        'expires_at': active_code['expires_at']
    })

@api.route('/api/revoke-code', methods=['POST'])
@login_required
def api_revoke_code():
    """Révoque le code actif"""
    if revoke_code():
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Aucun code actif'})

# ==================== EMAIL ====================

@api.route('/api/email-config', methods=['POST'])
@login_required
def api_email_config():
    """Configure les notifications email"""
    data = request.get_json()
    enabled = data.get('enabled', False)
    address = data.get('address', '')
    
    if enabled and address:
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$'
        if not re.match(email_regex, address):
            return jsonify({'success': False, 'error': 'Adresse email invalide'})
    
    email_config['enabled'] = enabled
    email_config['address'] = address
    save_data()
    
    if enabled and address:
        add_event(f"Notifications email: {address}", "system")
    else:
        add_event("Notifications email désactivées", "system")
    
    return jsonify({'success': True})

# ==================== PUSH ====================

@api.route('/api/push-subscribe', methods=['POST'])
@login_required
def api_push_subscribe():
    """Enregistre un abonnement push"""
    sub_data = request.get_json()
    save_subscription(sub_data)
    return jsonify({'success': True})

@api.route('/api/vapid-key')
def api_vapid_key():
    """Retourne la clé publique VAPID"""
    return jsonify({'public_key': VAPID_PUBLIC_KEY})

# ==================== EVENTS ====================

@api.route('/api/events')
@login_required
def api_events():
    """Retourne l'historique des événements"""
    return jsonify({'events': events_log})

@api.route('/api/clear-events', methods=['POST'])
@login_required
def api_clear_events():
    """Vide l'historique des événements"""
    events_log.clear()
    add_event("Historique effacé", "system")
    return jsonify({'success': True})