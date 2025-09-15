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
def get_sheet_data(sheet_url: str):
    """
    Descarga datos desde Google Sheets (formato CSV).
    Devuelve un diccionario con meta (valor, fecha, lugar) y lista de participantes.
    """
    response = requests.get(sheet_url)
    response.raise_for_status()
    
    lines = response.text.splitlines()
    reader = csv.DictReader(lines)

    meta = {}
    participantes = []
    header_found = False

    for row in reader:
        # Detectar encabezado real
        if row['SORTEO AMIGO SECRETO 2025'] == "Nombres" and row[''] == "Telefono":
            header_found = True
            continue

        if not header_found:
            # Guardar metadatos
            clave = row['SORTEO AMIGO SECRETO 2025']
            valor = row['']
            if clave and valor:
                meta[clave] = valor
        else:
            # Guardar participantes
            participantes.append({
                "Nombres": row['SORTEO AMIGO SECRETO 2025'],
                "Telefono": row['']
            })

    return meta, participantes

# ---------------------------------
# Función para hacer el sorteo
# ---------------------------------
def hacer_sorteo(participantes):
    """
    Asigna cada participante con un amigo secreto diferente.
    Repite hasta lograr un sorteo válido.
    """
    nombres = [p["Nombres"] for p in participantes]

    while True:  # intentar hasta que salga un sorteo válido
        disponibles = nombres.copy()
        asignacion = {}
        valido = True

        for nombre in nombres:
            opciones = [d for d in disponibles if d != nombre]
            if not opciones:
                valido = False
                break  # sorteo inválido, se reinicia
            elegido = random.choice(opciones)
            asignacion[nombre] = elegido
            disponibles.remove(elegido)

        if valido:
            return asignacion

# ---------------------------
# Generar mensaje inicial
# ---------------------------
def generar_mensaje_inicial(quien, asignado, meta):
    valor = meta.get("VALOR DEL REGALO", "").lower()
    fecha = meta.get("FECHA Y HORA", "").lower()
    lugar = meta.get("LUGAR", "").lower()

    return (
        f"Hola {quien}, tu Amigo Secreto es {asignado}.\n"
        f"Recuerda que es el {fecha} en la dirección {lugar} "
        f"y el regalo debe ser de {valor}.\n"
        f"¡No lo olvides!"
    )

# ---------------------------
# Generar mensaje recordatorio
# ---------------------------
def generar_mensaje_recordatorio(quien, meta):
    valor = meta.get("VALOR DEL REGALO", "").lower()
    fecha = meta.get("FECHA Y HORA", "").lower()
    lugar = meta.get("LUGAR", "").lower()

    return (
        f"{quien}, listo para jugar Amigo Secreto.\n"
        f"¿Ya compraste el regalo? \n"
        f"Recuerda que nos vemos mañana {fecha}\n"
        f"¡No faltes!"
    )

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
# MAIN
# ---------------------------------
if __name__ == "__main__":

    show_prints = True
    send_messages = True
    send_messages_reminder = False

    # URL de tu Google Sheets en formato CSV
    URL = "https://docs.google.com/spreadsheets/d/1eH4JdXV-uSmgjKpaoNXsE4JL_ksc9f5R6wuYt8n_rUg/export?format=csv"

    ALTIRIA_API_KEY = os.getenv("ALTIRIA_API_KEY")
    ALTIRIA_API_SECRET = os.getenv("ALTIRIA_API_SECRET")

    meta, participantes = get_sheet_data(URL)

    if show_prints:
        print("📌 Datos del sorteo:")
        print(f"Valor del regalo: {meta.get('VALOR DEL REGALO')}")
        print(f"Fecha y hora: {meta.get('FECHA Y HORA')}")
        print(f"Lugar: {meta.get('LUGAR')}")

        print("📋 Participantes:")
        for p in participantes:
            print(p)

    # === HACER EL SORTEO (Amigo Dulce) ===
    asignacion = hacer_sorteo(participantes)

    # === ENVIAR MENSAJES INICIALES ===
    if send_messages:
        for p in participantes:
            quien = p["Nombres"]
            telefono = "57" + p["Telefono"]
            asignado = asignacion[quien]

            mensaje = generar_mensaje_inicial(quien, asignado, meta)
            altiria_sms(ALTIRIA_API_KEY, ALTIRIA_API_SECRET, telefono, mensaje)
            if show_prints:
                print(f"📩 {mensaje} → {telefono}")


    # === ENVIAR MENSAJES RECORDATORIO ===
    if send_messages_reminder:
        for p in participantes:
            quien = p["Nombres"]
            telefono = "57" + p["Telefono"]

            mensaje = generar_mensaje_recordatorio(quien, meta)
            altiria_sms(ALTIRIA_API_KEY, ALTIRIA_API_SECRET, telefono, mensaje)
            print(f"📩 Recordatorio a {telefono}:\n{mensaje}\n")

            if show_prints:
                print(f"📩 {mensaje} → {telefono}")

    print("✅ Mensajes enviados.")