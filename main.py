import requests
import csv
from dotenv import load_dotenv
import os
import random
import json

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
# Función para enviar SMS usando Altiria (API Key + Secret)
# ---------------------------------
def altiria_sms(api_key: str, api_secret: str, phone: str, message: str, debug: bool = True):
    """
    Envía un SMS usando Altiria API Key + Secret.
    """
    url = "https://www.altiria.net:8443/apirest/ws/sendSms"
    headers = {"Content-Type": "application/json;charset=UTF-8"}

    payload = {
        "credentials": {"apiKey": api_key, "apiSecret": api_secret},
        "destination": [phone],
        "message": {"msg": message}
    }

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=(5, 60))

        if debug:
            print(f"📨 Enviando SMS a {phone}: {message}")

        if response.status_code != 200:
            print("❌ Error HTTP:", response.status_code, response.text)
            return {"success": False, "error": response.text}

        resp_json = response.json()
        if debug:
            print("✅ Respuesta Altiria:", json.dumps(resp_json, indent=2, ensure_ascii=False))

        if resp_json.get("status") != "000":
            return {"success": False, "error": resp_json}

        return {"success": True, "data": resp_json}

    except requests.ConnectTimeout:
        print("⏱️ Tiempo de conexión agotado")
        return {"success": False, "error": "Timeout de conexión"}
    except requests.ReadTimeout:
        print("⏱️ Tiempo de respuesta agotado")
        return {"success": False, "error": "Timeout de lectura"}
    except Exception as ex:
        print("⚠️ Error interno:", str(ex))
        return {"success": False, "error": str(ex)}


# ---------------------------------
# Lógica principal
# ---------------------------------
if __name__ == "__main__":
    # URL de tu Google Sheets en formato CSV
    URL = "https://docs.google.com/spreadsheets/d/1eH4JdXV-uSmgjKpaoNXsE4JL_ksc9f5R6wuYt8n_rUg/export?format=csv"

    ALTIRIA_API_KEY = os.getenv("ALTIRIA_API_KEY")
    ALTIRIA_API_SECRET = os.getenv("ALTIRIA_API_SECRET")

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
        telefono = "57" + p["Telefono"]
        asignado = asignacion[quien]

        mensaje = f"🎁 Hola {quien}, tu Amigo secreto es {asignado}. ¡Guárdalo en secreto! 🤫🍫"
        altiria_sms(ALTIRIA_API_KEY, ALTIRIA_API_SECRET, telefono, mensaje)

    print("✅ Mensajes enviados.")