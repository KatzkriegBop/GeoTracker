from typing import Final
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import time

TOKEN: Final = '7365320575:AAEW3lXlLMAi7FHYrV_W96hfNXasZTKKCT0'
BOT_USERNAME: Final = '@G30_807bot'

seguimiento_activo = set()
ultimas_ubicaciones = {}
jobs_por_usuario = {}
seguimiento_telefonos = {}  # user_id -> teléfono

FIREBASE_URL = "https://movigeotracker-default-rtdb.firebaseio.com"

def guardar_ubicacion_en_firebase(telefono: str, lat: float, lon: float):
    timestamp = int(time.time())
    url = f"{FIREBASE_URL}/ubicaciones/{telefono}/{timestamp}.json"
    data = {
        "lat": lat,
        "lon": lon
    }
    try:
        response = requests.put(url, json=data)
        if response.status_code != 200:
            print(f"[Firebase] Error al guardar ubicación: {response.text}")
        else:
            print(f"[Firebase] Ubicación guardada para {telefono} en timestamp {timestamp}")
    except Exception as e:
        print(f"[Firebase] Excepción: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("📞 Compartir número", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Bienvenido a GeoTracker.\n\nAntes de comenzar necesito que compartas tu número de teléfono para registrar tu ubicación.",
        reply_markup=reply_markup
    )

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.contact:
        return

    user_id = str(update.effective_user.id)
    telefono = update.message.contact.phone_number
    seguimiento_telefonos[user_id] = telefono

    keyboard = [
        [KeyboardButton("Enviar ubicación manual", request_location=True)],
        [KeyboardButton("Activar Seguimiento")],
        [KeyboardButton("Desactivar Seguimiento")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"✅ Número registrado correctamente: {telefono}\n\nAhora puedes activar el seguimiento o enviarme tu ubicación.",
        reply_markup=reply_markup
    )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.location:
        return

    user_id = str(update.effective_user.id)
    telefono = seguimiento_telefonos.get(user_id)
    if not telefono:
        await update.message.reply_text("⚠️ Primero debes compartir tu número de teléfono usando el botón correspondiente.")
        return

    location = update.message.location

    if user_id not in seguimiento_activo:
        await update.message.reply_text("Ubicación recibida, pero el seguimiento está desactivado.")
        return

    ultimas_ubicaciones[user_id] = {
        "lat": location.latitude,
        "lon": location.longitude
    }

    guardar_ubicacion_en_firebase(
        telefono,
        location.latitude,
        location.longitude
    )

    print(f"Ubicación recibida de {telefono}: {ultimas_ubicaciones[user_id]}")
    await update.message.reply_text("Ubicación registrada correctamente (seguimiento activo).")

async def enviar_ubicacion_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    user_id = str(job.chat_id)

    ubicacion = ultimas_ubicaciones.get(user_id)
    telefono = seguimiento_telefonos.get(user_id)

    if telefono and ubicacion:
        print(f"[JobQueue 1s] {telefono}: {ubicacion}")
    else:
        print(f"[JobQueue 1s] {user_id}: Sin ubicación registrada o teléfono no compartido.")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = str(update.effective_user.id)
    telefono = seguimiento_telefonos.get(user_id)
    text = update.message.text

    if not telefono:
        await update.message.reply_text("⚠️ Por favor comparte tu número de teléfono antes de continuar.")
        return

    if text == "Activar Seguimiento":
        seguimiento_activo.add(user_id)

        if user_id not in jobs_por_usuario:
            job = context.job_queue.run_repeating(enviar_ubicacion_job, interval=1.0, chat_id=update.effective_chat.id)
            jobs_por_usuario[user_id] = job

        await update.message.reply_text(
            "✅ Seguimiento activado.\n\n📍 Comparte tu ubicación en tiempo real desde Telegram:\n"
            "1. Toca el clip (📎) o el botón de adjuntar.\n"
            "2. Selecciona *Ubicación*.\n"
            "3. Luego elige *Ubicación en tiempo real*.\n\n"
            "Yo registraré tu ubicación automáticamente."
        )

    elif text == "Desactivar Seguimiento":
        seguimiento_activo.discard(user_id)

        job = jobs_por_usuario.pop(user_id, None)
        if job:
            job.schedule_removal()

        await update.message.reply_text("❌ Seguimiento desactivado.")

    elif text == "Enviar ubicación manual":
        await update.message.reply_text("📍 Toca el botón para enviarme tu ubicación actual.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    user_text: str = update.message.text
    response: str = handle_response(user_text)
    print(f"Received message from {update.message.chat.id} ({message_type}): {user_text}")
    await update.message.reply_text(response)

def handle_response(text: str):
    processed: str = text.lower()
    if 'track me' in processed:
        return "Tracking your location..."
    else:
        return "I didn't understand that. Can you please rephrase?"

if __name__ == '__main__':
    print("Starting the bot...")
    application = Application.builder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler('start', start_command))
    #application.add_handler(CommandHandler('help', help_command))
    #application.add_handler(CommandHandler('track', track_command))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    print("Bot is running...")
    application.run_polling(poll_interval=3, timeout=10)
