# Gestion des notifications push WebPush

import json
import os
import base64
from py_vapid import Vapid
from pywebpush import webpush, WebPushException
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption, PublicFormat

# Fichier où on stocke les abonnements
SUBS_FILE = 'push_subscriptions.json'

# Clés VAPID
VAPID_PRIVATE_KEY = None
VAPID_PUBLIC_KEY  = None
VAPID_CLAIMS      = {"sub": "mailto:smartbox@example.com"}

subscriptions = []

def init_vapid():
    global VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY

    if os.path.exists('vapid_keys.json'):
        with open('vapid_keys.json') as f:
            keys = json.load(f)
        VAPID_PRIVATE_KEY = keys['private']
        VAPID_PUBLIC_KEY  = keys['public']
    else:
        vapid = Vapid()
        vapid.generate_keys()

        # Clé privée en base64 urlsafe
        priv_bytes = vapid.private_key.private_bytes(
            Encoding.DER, PrivateFormat.PKCS8, NoEncryption()
        )
        VAPID_PRIVATE_KEY = base64.urlsafe_b64encode(priv_bytes).decode()

        # Clé publique en base64 urlsafe
        pub_bytes = vapid.public_key.public_bytes(
            Encoding.X962, PublicFormat.UncompressedPoint
        )
        VAPID_PUBLIC_KEY = base64.urlsafe_b64encode(pub_bytes).rstrip(b'=').decode()

        with open('vapid_keys.json', 'w') as f:
            json.dump({'private': VAPID_PRIVATE_KEY, 'public': VAPID_PUBLIC_KEY}, f)

    print(f"VAPID Public Key: {VAPID_PUBLIC_KEY}")
    load_subscriptions()
    return VAPID_PUBLIC_KEY

def load_subscriptions():
    global subscriptions
    if os.path.exists(SUBS_FILE):
        with open(SUBS_FILE) as f:
            subscriptions = json.load(f)

def save_subscription(sub_data):
    endpoint = sub_data.get('endpoint')
    subscriptions[:] = [s for s in subscriptions if s.get('endpoint') != endpoint]
    subscriptions.append(sub_data)
    with open(SUBS_FILE, 'w') as f:
        json.dump(subscriptions, f)

def send_push_notification(title, body, tag='smartbox'):
    if not subscriptions:
        print("[PUSH] Aucun abonné")
        return

    payload = json.dumps({'title': title, 'body': body, 'tag': tag})
    dead = []

    for sub in subscriptions:
        try:
            webpush(
                subscription_info=sub,
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
            print(f"[PUSH] Envoyé : {title}")
        except WebPushException as e:
            if e.response and e.response.status_code in (404, 410):
                dead.append(sub)
            else:
                print(f"Push erreur WebPush: {e}")
        except Exception as e:
            print(f"Push erreur: {e}")

    for s in dead:
        subscriptions.remove(s)
    if dead:
        with open(SUBS_FILE, 'w') as f:
            json.dump(subscriptions, f)