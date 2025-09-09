import requests
import csv
from dotenv import load_dotenv
import os
import random

load_dotenv()

# ---------------------------------
# Función para obtener participantes desde Google Sheets
# ---------------------------------
def get_participants(sheet_url: str):
    """
    Descarga participantes desde un Google Sheets (formato CSV).
    """
    response = requests.get(sheet_url)
    response.raise_for_status()  # lanza excepción si falla
    
    participantes = list(csv.DictReader(response.text.splitlines()))
    return participantes

# ---------------------------------
# Función para enviar SMS usando SMS Chef
# ---------------------------------
def send_sms(secret: str, phone: str, message: str, sim: int = 1, mode: str = "devices"):
    """
    Envía un SMS usando la API de SMS Chef.
    """
    url = "https://www.cloud.smschef.com/api/send/sms"
    data = {
        "secret": secret,
        "mode": mode,
        "phone": phone,
        "message": message,
        "sim": sim
    }

    response = requests.post(url, data=data)

    print(f"📨 Enviando SMS a {phone}: {message}")

    if response.status_code == 200:
        print("✅ Respuesta SMS Chef:", response.json())
        return {"success": True, "data": response.json()}
    else:
        print("❌ Error SMS Chef:", response.status_code, response.text)
        return {"success": False, "error": response.json()}

# ---------------------------------
# Lógica principal
# ---------------------------------
if __name__ == "__main__":
    # URL de tu Google Sheets en formato CSV
    URL = "https://docs.google.com/spreadsheets/d/1eH4JdXV-uSmgjKpaoNXsE4JL_ksc9f5R6wuYt8n_rUg/export?format=csv"
    API_KEY = os.getenv("SMS_CHEF_API_KEY")

    participantes = get_participants(URL)

    print("📋 Participantes:")
    for p in participantes:
        print(p)
    
    # === HACER EL SORTEO (Amigo Dulce) ===
    nombres = [p["Nombre"] for p in participantes]
    disponibles = nombres.copy()
    asignacion = {}

    for nombre in nombres:
        opciones = [d for d in disponibles if d != nombre]
        elegido = random.choice(opciones)
        asignacion[nombre] = elegido
        disponibles.remove(elegido)

    # === ENVIAR MENSAJES ===
    for p in participantes:
        quien = p["Nombre"]
        telefono = "+57" + p["Telefono"] 
        asignado = asignacion[quien]

        mensaje = f"🎁 Hola {quien}, tu Amigo Dulce es {asignado}. ¡Guárdalo en secreto! 🤫🍫"
        send_sms(API_KEY, telefono, mensaje)
