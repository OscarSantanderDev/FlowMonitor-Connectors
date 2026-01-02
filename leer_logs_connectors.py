import os
import re
import smtplib

from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_email(sitio, datos):
    try:
        subject = f"Asrun Procesados por Connectors."
        body = f" Archivos procesados en Connectors {sitio}.\n\n"
        for dato in datos:
            body += "\n" + dato
        sender_email = "asrconnectors@televisaunivision.com"
        receiver_email = "restevap@televisaunivision.com"

        
        destinos = ['restevap@televisaunivision.com', 'oesantanderb@televisaunivision.com']
        # Create a multipart message and set headers
        # destinos = ['oesantanderb@televisaunivision.com']
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message["Bcc"] = receiver_email  # Recommended for mass emails

        # Add body to email
        message.attach(MIMEText(body, "plain"))

        text = message.as_string()

        server = smtplib.SMTP('10.1.98.12')
        server.set_debuglevel(0)
        server.sendmail(sender_email, destinos, text)
        server.quit()

    except Exception as e:
        print(e)
        print("[mail] Error en función")


def construye_fecha(hora_str):
    try:
        hoy = datetime.now()
        hora_str = hora_str.replace('a. m.', 'AM').replace('P. m.', 'PM')
        hora_obj = datetime.strptime(hora_str, "%I:%M:%S %p")

        fecha = hoy.replace(
            hour=hora_obj.hour,
            minute=hora_obj.minute,
            second=hora_obj.second,
            microsecond=0
        )

        return fecha.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as err:

        return ''

def obtener_bitacora_asr():

    paths = ["W:/CajasNegras/logs/Logs Connectos Centralizados/",  "W:/CajasNegras/logs/Logs Connectos Santa Fe/"]

    today = datetime.now()
    fecha_formateada = today.strftime("%y%m%d")

    regex_asr = re.compile(r"([a-zA-Z0-9]{2}\d{8}a\.ASR)")

    contenido = []
    archivos = {}

    try:
        for path in paths:
            with os.scandir(path) as files:
                for file in files:
                    if fecha_formateada in file.name:
                        sitio = 'CHA' if "Centralizados" in path else 'SFE'

                        with open(path + file.name, 'r') as archivo:
                            for linea in archivo:
                                archivo = str()
                                # print(linea.strip())
                                contenido.append(linea)
                                if 'Transferencia' in linea.strip():
                                    match = regex_asr.search(linea)
                                    archivo = match.group(1) if match else ''

                                    if archivo:
                                        lmk_code = archivo[:2]
                                        tmp = {'archivo': archivo,'fecha': construye_fecha(linea[:14]), 'sitio': sitio, 'log': linea.strip()}
                                        archivos.setdefault(lmk_code, tmp)
                                    # print(linea.strip(), ' --> ' , archivo, ' --> ' , construye_fecha(linea[:14]), ' --> ' , sitio)
    except Exception as err:
        print('Error al obtener bitacora connectors de ASR')
        
    # print(archivos)
    return archivos