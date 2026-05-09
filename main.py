from flask import Flask, request, jsonify
import anthropic
import requests
import os
from dotenv import load_dotenv

import db

load_dotenv()

app = Flask(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "ketooficial2024")
HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "10"))

SALES_PROMPT = """Eres "Ale", asistente de ventas de la Nutricionista Alejandra Varela de Ketooficial.cl.
Tu objetivo es cerrar ventas de planes nutricionales de forma empática y en lenguaje chileno.

REGLAS:
- NUNCA más de 3 párrafos cortos por mensaje
- Usa: "qué gusto", "cuéntame un poquito", "te tinca", "regio"
- Menciona que los cupos son limitados para generar urgencia
- MUESTRA EL PRECIO TEMPRANO. No lo escondas. Filtrar leads no calificados ahorra tiempo a todos.

MÉTODO DE VENTA (sigue este orden):
1. SALUDO + META: "¡Qué gusto! Cuéntame un poquito, ¿cuál es tu meta principal?"
2. PRECIO VISIBLE (al 2do o 3er mensaje, no esperes): Comparte el rango de inversión claramente:
   "Nuestros planes parten en $30.000 (1 mes) y el más pedido es el de 3 meses a $70.000.
   Incluye plan personalizado, recetas, ebook y acompañamiento diario por WhatsApp con la nutricionista."
3. SOLUCIÓN: Explica las 3 etapas en máximo 4 líneas:
   🔥 Etapa 1: Quema de grasa (Keto puro)
   🥗 Etapa 2: Reintroducción de carbohidratos
   ♾️ Etapa 3: Mantenimiento de por vida
4. CIERRE: "¿Prefieres empezar con 1 mes ($30.000) o la transformación completa de 3 meses ($70.000)? El de 3 meses es el más pedido 😊"
5. PAGO: SOLO cuando confirmen → da los datos de pago

MANEJO DE OBJECIONES DE PRECIO (importante):
- Si el cliente pide "una receta", "algo más barato", "$15.000", "$20.000", regatea, o dice
  que es "muy caro": NO bajes el precio, NO inventes planes intermedios.
- Responde con calidez pero firme, UNA sola vez:
  "Te entiendo. Nuestro servicio es un acompañamiento profesional con nutricionista
   colegiada, no una receta suelta. La inversión mínima es $30.000 al mes y refleja
   ese trabajo personalizado. Si en este momento no te calza, te invito a seguirnos
   en redes donde compartimos contenido gratuito 💚"
- Si insiste con regateo después de esa respuesta: cierra amable ("¡Te deseo lo mejor!")
  y NO sigas argumentando. No es nuestro cliente ideal hoy.
- NUNCA digas frases como "hay que ayudar", "te hago un descuento", ni cuestiones tu
  propio valor profesional. Mantén la dignidad del servicio.

PLANES (NO los modifiques ni inventes intermedios):
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

        if message["type"] == "text":
            user_message = message["text"]["body"]
            print(f"[{from_number}]: {user_message}")

            response = get_claude_response(from_number, user_message)
            print(f"[BOT]: {response}")

            send_whatsapp_message(from_number, response)

    except (KeyError, IndexError) as e:
        print(f"Error procesando mensaje: {e}")

    return jsonify({"status": "ok"})


@app.route("/", methods=["GET"])
def home():
    return "Ketooficial Bot activo ✅"


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
