import json

from ftplib import FTP
from pathlib import Path
from datetime import datetime, timedelta


import smtplib

from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def obtener_config():
    config_path = Path(__file__).resolve().parent / 'config.json'

    with config_path.open('r') as f:
        data_config = json.load(f)

    return data_config

def obtener_fecha():

    hoy = datetime.now()
    ayer = hoy - timedelta(days=1)
    
    return ayer.strftime("%Y%m%d")

def fechahora_ftp_archivo(info):

    try:
        if info.startswith('213'):
            date_str = info[4:]  # Extrae la parte de la fecha y hora
            
            date_file = datetime.strptime(date_str, '%Y%m%d%H%M%S')
            date_file = date_file - timedelta(hours=6)

            return f"{date_file}"

    except Exception as e:
        print('Error al obtener información del archivo')
        print(e)

        return "Sin Información"

def getFtpFiles(ruta = "/"):

    config = obtener_config()

    ftp_status = config['SERVIDOR']['ftp_estatus']
    ftp_config = config['FTP'][ftp_status]
    print(ftp_config)
    archivos_procesados = dict()

    fecha_consulta = obtener_fecha()
    print(fecha_consulta)
    try:
        ftp_in = FTP(ftp_config['ftp_host'])
        ftp_in.login(user=ftp_config['ftp_user'], passwd=ftp_config['ftp_pass'])
        ftp_in.cwd('/LMK_FTP/ASRUN/IN/Processed')

        archivos = ftp_in.nlst()
        # print(archivos)
        for f in archivos:
            if f.upper().endswith(".ASR") and fecha_consulta in f:
                # print(f"Archivo nuevo: {f}")
                if not f[:2] in archivos_procesados:
                    detalle_archivo = fechahora_ftp_archivo(ftp_in.sendcmd(f'MDTM {f}'))
                    info_file = {'archivo': f, 'fecha': detalle_archivo}
                    archivos_procesados.setdefault(f[:2], info_file)
                
                

        ftp_in.quit()

        # print(f"Archivos Procesados. {archivos_procesados}")
        # envio_notificacion(archivos_procesados)
        print(archivos_procesados)
    except Exception as err:
        print("Error al obtener los archivos del FTP")
        print(err)


def envio_notificacion(datos):

    config = obtener_config()


    mensaje = ""

    if datos:

        try:
            mensaje += "<br>Resumen:<br><br>"

            asunto_correo = "Resumen diario"
            
            subject = asunto_correo
            body = mensaje
            sender_email = config['WD']['commTraffic']['email_orig']

            destinos = config['WD']['commTraffic']['email_dest']

            #destinos = ['oesantanderb@televisaunivision.com', 'amaldonadol@televisaunivision.com']

            receiver_email = ", ".join(destinos)

            # Create a multipart message and set headers
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = receiver_email
            message["Subject"] = subject
            message["Bcc"] = receiver_email  # Recommended for mass emails

            # Add body to email
            message.attach(MIMEText(body, "html"))

            text = message.as_string()

            server = smtplib.SMTP('10.1.98.12')
            server.set_debuglevel(0)
            server.sendmail(sender_email, destinos, text)
            server.quit()

        except Exception as e:
            print('Error al generar correo')
            print(e)


getFtpFiles()