import json
import time

from ftplib import FTP
from pathlib import Path
from datetime import datetime, timedelta


import smtplib

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
    
def str_a_datetime(hora_str):
    ahora = datetime.now()
    
    h, m = map(int, hora_str.split(':'))
    fecha_programada = ahora.replace(hour=h, minute=m, second=0, microsecond=0)
    
    if fecha_programada <= ahora:
        return False
    #     fecha_programada += timedelta(days=1)
        
    return fecha_programada

def getFtpFiles(ruta = "/"):

    config = obtener_config()

    ftp_status = config['SERVIDOR']['ftp_estatus']
    ftp_config = config['FTP'][ftp_status]
    
    # print(ftp_config)
    archivos_procesados = dict()


    fecha_consulta = obtener_fecha()
    # print(fecha_consulta)
    try:
        ftp_in = FTP(ftp_config['ftp_host'])
        ftp_in.login(user=ftp_config['ftp_user'], passwd=ftp_config['ftp_pass'])
        ftp_in.cwd(ftp_config['ruta'])
        debug('INFO', 'Leyendo archivos en FTP')
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
        resumen = generar_reporte_html(archivos_procesados)
        envio_notificacion(resumen)
        # print(archivos_procesados)
        
    except Exception as err:
        print("Error al obtener los archivos del FTP")
        print(err)

def generar_reporte_html(archivos: dict):
    config = obtener_config()

    canales_usa = config['GRUPOS']['USA']
    canales_opc = config['GRUPOS']['OPC']
    plataformas = config['PLATAFORMAS']

    reporte_html = "<pre>"
    asr_faltantes = False

    for plataforma in plataformas:
        for canal in plataformas[plataforma].keys():
            lmk_code = plataformas[plataforma][canal]['lmk_code']
            log_code = plataformas[plataforma][canal]['extension']
            usa_info = '(USA)' if lmk_code in canales_usa else ''
            opc_info = True if lmk_code in canales_opc else False
            if lmk_code:
                if lmk_code in archivos.keys():
                    # print(f"{plataforma:<6} {usa_info:<10}🟢({log_code:<4}): {archivos[lmk_code]['archivo']:<20} [ftp_time: {archivos[lmk_code]['fecha']}]")
                    reporte_html += f"{plataforma:<10} {usa_info:<6}🟢 ({log_code +')':<8}: {archivos[lmk_code]['archivo']:<20} [ftp_time: {archivos[lmk_code]['fecha']}]<br>"
                else:
                    # print(f"{plataforma:>6} {usa_info:<10}🔴({log_code:<4}):")
                    reporte_html += f"{plataforma:<10} {usa_info:<6}🔴 ({log_code +')':<8}:<br>"
                    if not opc_info:
                        asr_faltantes = True

    reporte_html += "</pre>"

    if asr_faltantes:
        nueva_tarea = config['SERVIDOR']['horarios'][1]
        run_time = str_a_datetime(nueva_tarea)

        if run_time:
            scheduler.add_job(
                getFtpFiles, 
                'date', run_date=run_time,
                id=f'extra_job_{nueva_tarea}', # ID Único
                replace_existing=True
            )
            debug('!!!!', f'ASR Faltantes. Fue generada nueva tarea a las {run_time}')

    return reporte_html

def envio_notificacion(resumen):

    config = obtener_config()

    ftp_status = config['SERVIDOR']['ftp_estatus']
    ftp_config = config['FTP'][ftp_status]

    mensaje = ""

    try:
        mensaje += f"<br>Estatus de ASR en ftp ({ftp_config['ftp_host']}:{ftp_config['ruta']}):<br><br>"

        hoy = datetime.now()

        asunto_correo = f"Resumen diario. ({hoy.strftime("%Y-%m-%d")})"
        
        subject = asunto_correo
        body = mensaje + resumen
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


def main():
    config = obtener_config()
    horarios = config['SERVIDOR']['horarios']

    hora_inicio = horarios[0]
    hora_lits = hora_inicio.split(':')

    debug('INFO', 'Iniciando tarea programada:')
    debug('INFO', f"La tarea se ejecutara en los horarios: {horarios}")


    scheduler.add_job(
        getFtpFiles,
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


main()
# getFtpFiles()
# generar_reporte_html()
