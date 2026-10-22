import os
import telebot
from flask import Flask, request
from groq import Groq
import urllib.parse
import matplotlib.pyplot as plt
import numpy as np
import io

# ======================================================
# CONFIGURACIÓN DE CLAVES (Usa variables de entorno en la nube)
# ======================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8839280096:AAHnvC5q6oRd43K2nLbE8bZJegqyAyYetbg")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

MODELOS_GROQ = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b"
]

historial_conversaciones = {}

SYSTEM_PROMPT = r"""
# Rol
Eres Rina 🌟, una tutora académica súper amigable, entusiasta, paciente y muy interactiva.

# REGLAS ESTRICTAS DE ESTILO VISUAL Y FORMATO
1. **TEXTO LIMPIO Y SIN BARRAS:** 
   - PROHIBIDO usar código LaTeX o tablas con barras (|). Usa listas con viñetas limpias (•).
   - CERO exceso de asteriscos. Redacta de forma natural.
2. **USO DE IMÁGENES:**
   - Circunferencias: `[GRAFICO_MATH: geometrico_circunferencia]`
   - Triángulos: `[GRAFICO_MATH: geometrico_triangulo]`
   - Mapas/Ciencias: `[MAPA_IA: descripción clara en inglés]`
   - Gramática/Teoría: No uses etiquetas de imagen.
3. **DINÁMICA:** Explica limpio, añade imagen si hace falta, usa `[SEPARADOR]`, y pon 1 o 2 ejercicios prácticos para evaluar al estudiante.
"""

# Funciones de dibujo (Matplotlib) igual que antes...
def generar_triangulo_rectangulo():
    try:
        plt.figure(figsize=(5, 5))
        x = [0, 4, 0, 0]
        y = [0, 0, 3, 0]
        plt.plot(x, y, color="#8A2BE2", linewidth=3)
        plt.fill(x, y, color="#E6E6FA", alpha=0.5)
        plt.text(2, -0.3, 'Cateto b (4 cm)', fontsize=11, ha='center', fontweight='bold', color='#333333')
        plt.text(-0.5, 1.5, 'Cateto a (3 cm)', fontsize=11, va='center', fontweight='bold', color='#333333')
        plt.text(2.2, 1.7, 'Hipotenusa c (5 cm)', fontsize=11, rotation=37, fontweight='bold', color='#8A2BE2')
        plt.plot([0, 0.4, 0.4, 0], [0, 0, 0.4, 0.4], color='black', linewidth=1.5)
        plt.xlim(-1, 5)
        plt.ylim(-1, 4)
        plt.axis('off')
        plt.title('Triángulo Rectángulo', fontsize=12, fontweight='bold', color='#4B0082')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        buf.seek(0)
        plt.close()
        return buf
    except:
        return None

def generar_circunferencia_esquema():
    try:
        fig, ax = plt.subplots(figsize=(5, 5))
        circulo = plt.Circle((0, 0), 3, color='#E6E6FA', ec='#8A2BE2', linewidth=3, alpha=0.6)
        ax.add_patch(circulo)
        ax.plot(0, 0, 'ro', markersize=6)
        ax.text(-0.3, -0.3, 'Centro', fontsize=10, fontweight='bold', color='#333333')
        ax.plot([0, 3], [0, 0], color='#FF4500', linestyle='--', linewidth=2.5)
        ax.text(1.5, 0.2, 'Radio (r)', fontsize=11, fontweight='bold', color='#FF4500')
        ax.plot([-3, 3], [-0.8, -0.8], color='#008080', linewidth=2)
        ax.text(0, -1.2, 'Diámetro (d)', fontsize=11, ha='center', fontweight='bold', color='#008080')
        ax.set_xlim(-4, 4)
        ax.set_ylim(-4, 4)
        ax.set_aspect('equal')
        ax.axis('off')
        plt.title('Circunferencia, Radio y Diámetro', fontsize=12, fontweight='bold', color='#4B0082')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        buf.seek(0)
        plt.close()
        return buf
    except:
        return None

def generar_grafico_matematico(expresion):
    if expresion == "geometrico_triangulo":
        return generar_triangulo_rectangulo()
    elif expresion == "geometrico_circunferencia":
        return generar_circunferencia_esquema()
    return None

def enviar_mensaje_seguro(chat_id, texto, reply_to_id=None):
    if not texto or not texto.strip():
        return
    LIMITE = 3500
    if len(texto) <= LIMITE:
        bot.send_message(chat_id, texto, reply_to_message_id=reply_to_id)
    else:
        for i in range(0, len(texto), LIMITE):
            parte = texto[i:i+LIMITE]
            if parte.strip():
                bot.send_message(chat_id, parte)

# Ruta que recibe los mensajes de Telegram automáticamente
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "¡Rina está activa en la nube!", 200

# Lógica del mensaje entrante
@bot.message_handler(func=lambda message: True)
def responder(message):
    chat_id = message.chat.id
    user_text = message.text

    if chat_id not in historial_conversaciones:
        historial_conversaciones[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    historial_conversaciones[chat_id].append({"role": "user", "content": user_text})

    texto_respuesta = None
    for modelo in MODELOS_GROQ:
        try:
            completion = client.chat.completions.create(
                model=modelo,
                messages=historial_conversaciones[chat_id],
                temperature=0.7,
            )
            texto_respuesta = completion.choices[0].message.content
            break
        except:
            continue

    if texto_respuesta:
        historial_conversaciones[chat_id].append({"role": "assistant", "content": texto_respuesta})
        
        prompt_mapa, expr_math = None, None
        if "[MAPA_IA:" in texto_respuesta:
            inicio = texto_respuesta.find("[MAPA_IA:") + 9
            fin = texto_respuesta.find("]", inicio)
            if fin != -1:
                prompt_mapa = texto_respuesta[inicio:fin].strip()
                texto_respuesta = texto_respuesta[:inicio-9] + texto_respuesta[fin+1:]

        if "[GRAFICO_MATH:" in texto_respuesta:
            inicio = texto_respuesta.find("[GRAFICO_MATH:") + 14
            fin = texto_respuesta.find("]", inicio)
            if fin != -1:
            # Corrección de índices internos
                expr_math = texto_respuesta[inicio:fin].strip()
                texto_respuesta = texto_respuesta[:inicio-14] + texto_respuesta[fin+1:]

        if "[SEPARADOR]" in texto_respuesta:
            partes = texto_respuesta.split("[SEPARADOR]")
            explicacion, ejercicios = partes[0].strip(), partes[1].strip()
            if explicacion:
                enviar_mensaje_seguro(chat_id, explicacion, reply_to_id=message.message_id)
            if prompt_mapa:
                url_img = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt_mapa)}?width=800&height=600&nologo=true"
                bot.send_photo(chat_id, url_img, caption="🖼️ Esquema conceptual")
            if expr_math:
                img_buf = generar_grafico_matematico(expr_math)
                if img_buf:
                    bot.send_photo(chat_id, img_buf, caption="📐 Esquema geométrico")
            if ejercicios:
                enviar_mensaje_seguro(chat_id, ejercicios)
        else:
            enviar_mensaje_seguro(chat_id, texto_respuesta, reply_to_id=message.message_id)

if __name__ == "__main__":
    # Configurar Webhook automáticamente al iniciar en la nube
    url_render = os.environ.get("RENDER_EXTERNAL_URL")
    if url_render:
        bot.remove_webhook()
        bot.set_webhook(url=f"{url_render}/{TELEGRAM_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))