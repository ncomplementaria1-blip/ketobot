from flask import Flask, request, jsonify
import anthropic
import requests
import os
import hashlib
import hmac
import time
import uuid
from dotenv import load_dotenv

import db

load_dotenv()

app = Flask(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "ketooficial2024")
HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "10"))

META_DATASET_ID = os.getenv("META_DATASET_ID")
META_CAPI_TOKEN = os.getenv("META_CAPI_TOKEN")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

SALES_PROMPT = """Eres "Ale", asistente de ventas de la Nutricionista Alejandra Varela de Ketooficial.cl.
Tu objetivo es cerrar ventas de planes nutricionales de forma empática y en lenguaje chileno.

REGLAS:
- NUNCA más de 3 párrafos cortos por mensaje
- SIEMPRE pregunta la meta del cliente ANTES de dar precios
- Usa: "qué gusto", "cuéntame un poquito", "te tinca", "regio"
- Menciona que los cupos son limitados para generar urgencia

MÉTODO DE VENTA (sigue este orden):
1. DIAGNÓSTICO: Si preguntan precio o info → pregunta: "¿Cuántos kilos te gustaría bajar o cuál es tu meta principal?"
2. SOLUCIÓN: Explica las 3 etapas en máximo 4 líneas:
   🔥 Etapa 1: Quema de grasa (Keto puro)
   🥗 Etapa 2: Reintroducción de carbohidratos
   ♾️ Etapa 3: Mantenimiento de por vida
3. CIERRE: "¿Prefieres empezar con 1 mes ($30.000) o la transformación completa de 3 meses ($70.000)? El de 3 meses es el más pedido 😊"
4. PAGO: SOLO cuando confirmen → da los datos de pago

PLANES:
- 1 mes: $30.000 CLP / $40 USD
- 2 meses: $50.000 CLP / $66 USD
- 3 meses: $70.000 CLP / $93 USD ⭐ más pedido

INCLUYE: Menú personalizado, Ebook, recetas, rutina de ejercicios, acompañamiento por WhatsApp

DATOS DE PAGO (solo al confirmar compra, da UN método a la vez):
- BancoEstado / Copec Pay / Prex: Alejandrina Varela Guevara / RUT 16100846K
- Webpay online: https://ketooficial.com/dieta-keto/
- Ficha clínica (tras pago): https://www.ketooficial.com/eforms/ficha-clinica/11/

Si el cliente pregunta algo de nutrición/keto, responde brevemente y redirige a la venta."""

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

db.init_db()


def get_claude_response(user_id, user_message):
    db.save_message(user_id, "user", user_message)
    history = db.get_conversation(user_id, limit=HISTORY_LIMIT)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        system=[
            {
                "type": "text",
                "text": SALES_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=history,
    )

    assistant_message = response.content[0].text
    db.save_message(user_id, "assistant", assistant_message)
    return assistant_message


def send_meta_purchase_event(user_id, value_clp, event_id):
    """Manda evento Purchase a Meta Conversions API para optimizar ads por compras.

    user_id es el número de teléfono del cliente (formato E.164 sin '+').
    value_clp es el monto en CLP. event_id evita doble conteo si se reenvía.
    """
    if not META_DATASET_ID or not META_CAPI_TOKEN:
        print("⚠️  META_DATASET_ID o META_CAPI_TOKEN no configurados — skip CAPI")
        return None

    phone_hash = hashlib.sha256(user_id.encode("utf-8")).hexdigest()
    ctwa_clid = db.get_user_referral(user_id)

    user_data = {"ph": [phone_hash]}
    if ctwa_clid:
        user_data["ctwa_clid"] = ctwa_clid

    payload = {
        "data": [
            {
                "event_name": "Purchase",
                "event_time": int(time.time()),
                "action_source": "business_messaging",
                "messaging_channel": "whatsapp",
                "event_id": event_id,
                "user_data": user_data,
                "custom_data": {"currency": "CLP", "value": value_clp},
            }
        ]
    }
    url = f"https://graph.facebook.com/v18.0/{META_DATASET_ID}/events"
    response = requests.post(
        url, params={"access_token": META_CAPI_TOKEN}, json=payload
    )
    print(f"[CAPI] Purchase {event_id} → {response.status_code} {response.text}")
    return response.json()


def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Meta llama esto para verificar que el servidor es tuyo."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    """Recibe mensajes de WhatsApp y responde con Claude."""
    data = request.json

    try:
        entry = data["entry"][0]
        value = entry["changes"][0]["value"]

        if "messages" not in value:
            return jsonify({"status": "ok"})

        message = value["messages"][0]
        from_number = message["from"]

        referral = message.get("referral") or {}
        ctwa_clid = referral.get("ctwa_clid")
        if ctwa_clid:
            db.upsert_user_referral(from_number, ctwa_clid)
            print(f"[CTWA] {from_number} viene del ad clid={ctwa_clid}")
        else:
            db.upsert_user_referral(from_number, None)

        if message["type"] == "text":
            user_message = message["text"]["body"]
            print(f"[{from_number}]: {user_message}")

            response = get_claude_response(from_number, user_message)
            print(f"[BOT]: {response}")

            send_whatsapp_message(from_number, response)

    except (KeyError, IndexError) as e:
        print(f"Error procesando mensaje: {e}")

    return jsonify({"status": "ok"})


@app.route("/admin/sale", methods=["POST"])
def admin_sale():
    """Marca una venta confirmada y dispara el evento Purchase a Meta CAPI.

    Body JSON: { "user_id": "56912345678", "value_clp": 30000, "event_id": "opcional" }
    Header: Authorization: Bearer <ADMIN_TOKEN>
    """
    if not ADMIN_TOKEN:
        return jsonify({"error": "ADMIN_TOKEN no configurado"}), 500

    auth = request.headers.get("Authorization", "")
    expected = f"Bearer {ADMIN_TOKEN}"
    if not hmac.compare_digest(auth, expected):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    value_clp = data.get("value_clp")
    if not user_id or not isinstance(value_clp, int):
        return jsonify({"error": "user_id y value_clp (int) son obligatorios"}), 400

    event_id = data.get("event_id") or f"sale-{uuid.uuid4()}"
    inserted = db.record_sale(user_id, value_clp, event_id)
    if not inserted:
        return jsonify({"status": "duplicate", "event_id": event_id}), 200

    meta_response = send_meta_purchase_event(user_id, value_clp, event_id)
    return jsonify({"status": "ok", "event_id": event_id, "meta": meta_response})


@app.route("/", methods=["GET"])
def home():
    return "Ketooficial Bot activo ✅"


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
