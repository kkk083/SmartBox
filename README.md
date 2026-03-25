# 📬 SmartBox — Boîte aux Lettres Connectée & Sécurisée

> Projet IoT — Université des Mascareignes | Informatique Appliquée | 2025/2026

**Membres du groupe :**
- Damien Salamero
- Marie Pulcherie Emie
- Junior Yissibi

---

## C'est quoi SmartBox ?

SmartBox c'est une boîte aux lettres intelligente qui combine deux fonctions dans un seul système connecté :

- **Un compartiment lettres** — le facteur glisse le courrier normalement, un laser détecte automatiquement l'arrivée du courrier
- **Un compartiment colis** — accès sécurisé par code temporaire, le livreur tape un code sur un clavier pour déposer un colis

Le tout est piloté par un **Arduino Mega** (capteurs et actionneurs) et un **Raspberry Pi** (logique, dashboard web, notifications), reliés par câble USB série.

---

## Fonctionnalités

- Génération de codes d'accès temporaires (30min, 1h, 2h ou durée personnalisée)
- Dashboard web accessible depuis n'importe quel appareil
- Notifications push sur smartphone (même app fermée)
- Notifications email
- Détection automatique de colis par capteur ultrason
- Détection automatique du courrier par faisceau laser
- Verrouillage automatique après fermeture de la porte
- Historique complet des événements
- Application installable sur téléphone (PWA)
- Dashboard protégé par login

---

## 🛠️ Matériel nécessaire

| Composant | Rôle |
|---|---|
| Raspberry Pi 3B+ ou 4 | Cerveau du système — héberge le dashboard |
| Arduino Mega 2560 | Gère les capteurs et actionneurs |
| Câble USB | Relie l'Arduino au Raspberry Pi |
| Keypad 4x4 | Clavier pour saisir le code |
| Servo SG90 | Verrouille/déverrouille la porte |
| LCD 16x2 + I2C | Affiche les instructions |
| Capteur ultrason HC-SR04 | Détecte la présence d'un colis |
| Module laser KY-008 + LDR | Détecte l'arrivée du courrier |
| Reed switch | Détecte si la porte est ouverte ou fermée |
| LED verte + LED rouge | Feedback visuel |
| Buzzer actif 5V | Feedback sonore |

---

## Structure du projet
```
SmartBox/
├── app.py              # Point d'entrée — lance le serveur Flask
├── config.py           # Configuration (login, port série, email...)
├── code_manager.py     # Génération et expiration des codes
├── email_handler.py    # Envoi des notifications email
├── models.py           # Données et état du système
├── push_handler.py     # Notifications push smartphone
├── routes.py           # Routes API Flask
├── serial_handler.py   # Communication avec l'Arduino
├── templates/
│   └── dashboard.html  # Interface web
└── static/
    ├── css/style.css   # Design du dashboard
    ├── js/app.js       # Logique frontend
    └── images/         # Icônes et image de fond
```

---

## Installation

### 1. Cloner ou copier le projet

Copie le dossier SmartBox sur ton Raspberry Pi :
```bash
scp -r "/chemin/vers/SmartBox" pi@IP_DU_PI:/home/pi/smartbox/
```

### 2. Créer un environnement virtuel
```bash
cd ~/smartbox
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances
```bash
pip install flask pyserial pywebpush py-vapid cryptography
```

### 4. Brancher l'Arduino

Connecte l'Arduino au Raspberry Pi avec un câble USB. Vérifie le port :
```bash
ls /dev/tty*
```

Note le port (généralement `/dev/ttyACM0`) et mets-le dans `config.py` :
```python
SERIAL_PORT = '/dev/ttyACM0'
```

### 5. Uploader le code Arduino

Ouvre `smartbox_mega.ino` dans l'IDE Arduino et uploade-le sur l'Arduino Mega.

### 6. Lancer le projet
```bash
source venv/bin/activate
python app.py
```

Le dashboard est accessible sur `http://IP_DU_PI:5000`

---

## Accès depuis l'extérieur (ngrok)

Si tu veux accéder au dashboard depuis n'importe où (pas seulement sur le WiFi local) :
```bash
./ngrok http --url=TON_DOMAINE.ngrok-free.dev 5000
```

---

## Installer la PWA sur smartphone

1. Ouvre le dashboard dans Chrome
2. Clique sur les 3 points → **Ajouter à l'écran d'accueil**
3. L'app s'installe comme une vraie application
4. Clique sur ** Activer les notifications** pour recevoir les alertes en temps réel

---

## Notifications push

Les notifications arrivent automatiquement sur ton téléphone quand :

-  Du courrier arrive
-  Un colis est déposé
-  Le livreur utilise le code correctement
-  Quelqu'un tape un mauvais code
-  Un colis est récupéré

---

## Comment ça marche
```
1. Tu génères un code temporaire depuis le dashboard
2. Tu envoies le code au livreur (SMS, mail...)
3. Le livreur tape le code sur le keypad de la boîte
4. L'Arduino vérifie le code → ouvre la porte
5. Le livreur dépose le colis et ferme la porte
6. Le capteur ultrason confirme la présence du colis
7. Tu reçois une notification sur ton téléphone
```

---

## Branchement Arduino

| Composant | Pin Arduino |
|---|---|
| Keypad 4x4 | D22, D24, D26, D28, D30, D32, D34, D36 |
| LCD I2C | SDA (pin 20), SCL (pin 21) |
| Servo SG90 | D9 |
| LED verte | D10 |
| LED rouge | D11 |
| Buzzer | D12 |
| Laser KY-008 | D13 |
| LDR | A0 |
| HC-SR04 Trig | A1 |
| HC-SR04 Echo | A2 |
| Reed switch | D2 |
| Bouton courrier | D5 |

---

## Configuration

Tout se configure dans `config.py` :
```python
# Login dashboard
AUTH_USER = 'admin'
AUTH_PASS = '1234'

# Port série Arduino
SERIAL_PORT = '/dev/ttyACM0'

# Email (optionnel)
EMAIL_CONFIG = {
    'enabled': False,
    'smtp_server': 'smtp.gmail.com',
    'smtp_user': 'ton.email@gmail.com',
    'smtp_pass': 'mot_de_passe_application'
}
```

---

## Protocole de communication Arduino ↔ Raspberry Pi

**Pi → Arduino :**
| Message | Action |
|---|---|
| `CODE:1234` | Active le code 1234 |
| `REVOKE` | Révoque le code actif |

**Arduino → Pi :**
| Message | Signification |
|---|---|
| `SMARTBOX_READY` | Arduino démarré |
| `MAIL_DETECTED` | Courrier reçu |
| `MAIL_CLEARED` | Courrier récupéré |
| `CODE_OK` | Code valide tapé |
| `CODE_FAIL` | Mauvais code tapé |
| `DOOR_OPENED` | Porte ouverte |
| `DOOR_CLOSED` | Porte fermée |
| `PARCEL_DETECTED` | Colis présent |
| `PARCEL_NONE` | Compartiment vide |

---

## Problèmes fréquents

**Arduino non détecté**
```
Arduino non connecté: could not open port '/dev/ttyACM0'
```
→ Vérifie le câble USB et le port dans `config.py`

**Notifications push ne marchent pas**
→ Le dashboard doit être ouvert en HTTPS (utilise ngrok)
→ Réactive les notifications dans le dashboard

**Le dashboard ne s'ouvre pas**
→ Vérifie que `python app.py` tourne bien sur le Pi
→ Vérifie que ton téléphone est sur le même réseau que le Pi

---

## Licence

Projet académique — Université des Mascareignes 2025/2026
