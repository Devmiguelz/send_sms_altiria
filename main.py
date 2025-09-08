import requests
import csv
from dotenv import load_dotenv
import os

load_dotenv()

# ---------------------------------
# Función para obtener participantes desde Google Sheets
# ---------------------------------
def get_participants(sheet_url: str):
    """
    Descarga participantes desde un Google Sheets (formato CSV).
    
    Args:
        sheet_url (str): URL de Google Sheets en formato CSV
    
    Returns:
        list[dict]: Lista de participantes con columnas como 'Nombre', 'Telefono', 'Email'
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

    Args:
        secret (str): API Secret de SMS Chef
        phone (str): Número del destinatario (ej: "573005997373")
        message (str): Contenido del mensaje
        sim (int): SIM a usar (1 por defecto)
        mode (str): Modo de envío, por defecto "devices"

    Returns:
        dict: Respuesta de la API de SMS Chef
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

    print(f"Enviando SMS a {phone}: {message}")

    print("Respuesta SMS Chef:", response.status_code, response.text)

    if response.status_code == 200:
        return {"success": True, "data": response.json()}
    else:
        return {"success": False, "error": response.json()}

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
    asignacion = {}

    for p in participantes:
        quien = p["Nombre"]
        telefono = "57" + p["Telefono"]  # agregamos el indicativo de país (ej: Colombia +57)
        asignado = asignacion[quien]

        mensaje = f"Hola {quien}, tu Amigo secreto es {asignado}. ¡Que sea secreto! 🤫"
        send_sms(API_KEY, telefono, mensaje)
