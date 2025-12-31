import json

from ftplib import FTP
from pathlib import Path
from datetime import datetime, timedelta

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


def obtener_config():
    config_path = Path(__file__).resolve().parent / 'config.json'

    with config_path.open('r') as f:
        data_config = json.load(f)

    return data_config

getFtpFiles()