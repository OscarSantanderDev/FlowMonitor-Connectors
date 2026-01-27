import json
import time
import pyodbc
import smtplib

from pathlib import Path

from datetime import datetime, timedelta

from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from apscheduler.schedulers.background import BackgroundScheduler


scheduler = BackgroundScheduler()


def debug(tipo, mensaje):
    print(f'[{tipo}] {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}. {mensaje}')

def obtener_config():
    config_path = Path(__file__).resolve().parent / 'config.json'

    with config_path.open('r') as f:
        data_config = json.load(f)

    return data_config

def obtener_fecha():

    hoy = datetime.now()
    ayer = hoy - timedelta(days=1)
    
    return ayer.strftime("%Y-%m-%d")



def envio_notificacion(resumen):

    config = obtener_config()

    db_status = config['SERVIDOR']['db_status']
    config_bd = config['DATABASE'][db_status]

    mensaje = ""

    try:
        mensaje += f"<br>Estatus de datos en BD ({config_bd['server']}:{config_bd['database']})<br><br>"

        asunto_correo = f"Reporte de Tx. Subida de datos ({obtener_fecha()})"
        
        subject = asunto_correo
        body = mensaje + resumen
        sender_email = config['WD']['reporteTx']['email_orig']

        destinos = config['WD']['reporteTx']['email_dest']

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


def obtener_registros_bd():

    config = obtener_config()
    db_status = config['SERVIDOR']['db_status']
    db = config['DATABASE'][db_status]

    asr, ply, concil = dict(), dict(), dict()

    try:
        connectionString = f"DRIVER={{SQL Server}};SERVER={db['server']};DATABASE={db['database']};UID={db['username']};PWD={db['password']}"

        fecha = obtener_fecha()

        conn = pyodbc.connect(connectionString) 
        cursor = conn.cursor()

        sql_asr = f"""SELECT fldCanal, COUNT(*) as n_registros
                FROM tblCsvAsr
                WHERE fldFechaLog = '{fecha}'
                GROUP BY fldCanal"""
        cursor.execute(sql_asr)
        # asr = cursor.fetchall()
        asr = {fila[0].strip(): fila[1] for fila in cursor.fetchall()}

        sql_ply = f"""SELECT fldCanal, COUNT(*) as n_registros
                FROM tblCsvAsr
                WHERE fldFechaLog = '{fecha}'
                GROUP BY fldCanal"""
        cursor.execute(sql_ply)
        # ply = cursor.fetchall()
        ply = {fila[0].strip(): fila[1] for fila in cursor.fetchall()}
        
        sql_concil = f"""SELECT fldCanal, COUNT(*) as n_registros
                FROM tblCsvAsr
                WHERE fldFechaLog = '{fecha}'
                GROUP BY fldCanal"""
        cursor.execute(sql_concil)
        # concil = cursor.fetchall()
        concil = {fila[0].strip(): fila[1] for fila in cursor.fetchall()}
        
        cursor.close()
        conn.close()

    except Exception as err:
        print('Error al guardar en la bd')
        print(err)

    return {'ply':ply ,'asr':asr ,'concil':concil}

def genera_reporte():
    datos = obtener_config()
    datos_bd = obtener_registros_bd()

    plataformas = datos['PLATAFORMAS']

    reporte_html = "<pre>"

    for plataforma in plataformas.keys():
        for canal in plataformas[plataforma].keys():

            tx_report = plataformas[plataforma][canal]['tx_report']
            asr_status = '🟢' if tx_report in datos_bd['asr'].keys() else '🔴' 
            ply_status = '🟢' if tx_report in datos_bd['ply'].keys() else '🔴' 
            concil_status = '🟢' if tx_report in datos_bd['concil'].keys() else '🔴'

            if tx_report:
                reporte_html += f"{plataforma:<12} {canal+':'+tx_report:<13} {asr_status+' asr':<7} {ply_status+' ply':<7} {concil_status+' concil':<7} <br>"

    reporte_html += "</pre>"

    envio_notificacion(reporte_html)

def main():
    config = obtener_config()
    horarios = config['SERVIDOR']['horarios_reporteTx']

    hora_inicio = horarios[0]
    hora_lits = hora_inicio.split(':')

    debug('INFO', 'Iniciando tarea programada:')
    debug('INFO', f"La tarea se ejecutara en los horarios: {horarios}")

    scheduler.add_job(
        genera_reporte,
        'cron',
        hour=int(hora_lits[0]), minute=int(hora_lits[1]),
        id=f"job_{hora_inicio}", # ID único basado en la hora
        replace_existing=True
    )
    debug('INFO', f"✅ Tarea programada para las {hora_inicio}")

    scheduler.start()

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


# main()
genera_reporte()
