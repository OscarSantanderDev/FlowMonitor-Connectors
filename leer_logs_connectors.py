import os
import smtplib

from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from datetime import datetime

today = datetime.now()
fecha_formateada = today.strftime("%y%m%d")

paths = ["W:/CajasNegras/logs/Logs Connectos Centralizados/",  "W:/CajasNegras/logs/Logs Connectos Santa Fe/"]
titulo = ""
contenido = []

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

for path in paths:
    with os.scandir(path) as files:
        for file in files:
            if fecha_formateada in file.name:
                if "Centralizados" in path:
                    titulo = "Centralizados"
                    print("Archivos procesados en Centralizados")
                else:
                    titulo = "Santa Fe"
                    print("Archivos procesados en Santa Fe")

                with open(path + file.name, 'r') as archivo:
                    for linea in archivo:
                        print(linea)
                        contenido.append(linea)
                
                send_email(titulo, contenido)