from app import get_db_conn
from time import sleep
import smtplib
from email.message import EmailMessage

# Datos del correo
email_remitente = 'jonathanelian64@gmail.com'
email_destinatario = 'hackelian89@gmail.com'
#email_destinatario = 'alfaroluis300705@gmail.com'
clave_app = 'uhjb qbnf tnze folf'  # No uses tu contraseña real

correos = [
    'diana.camacho@uas.edu.mx',
    'juancarlos@treintaiunminutos.com',
    'acastellnosmar@gmail.com',
    'hayala@uas.edu.mx'
]

def send_email(content, remitente, destinatario, asunto):
    """
    Envía un correo electrónico utilizando SMTP.
    
    :param content: Contenido del correo
    :param remitente: Correo del remitente
    :param destinatario: Correo del destinatario
    :param asunto: Asunto del correo
    """
    msg = EmailMessage()
    msg['Subject'] = asunto
    msg['From'] = remitente
    msg['To'] = destinatario
    msg.set_content(content)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(remitente, clave_app)
        smtp.send_message(msg)

    print("Correo enviado exitosamente 📨")


def watch():
    # observar cuando se vence el prestamo
    print("Iniciando el observador de prestamos vencidos...")
    while True:
        db_conn = get_db_conn()
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM prestamo WHERE fecha_devolucion < NOW()")

        datos = cursor.fetchall()

        if datos:
            for prestamo in datos:
                cursor.execute("SELECT correo FROM usuario WHERE id_usuario = %s", (prestamo[1],))
                user = cursor.fetchone()
                if user[0] in correos:
                    continue

                print(f"Prestamo vencido: {prestamo[0]} del usuario {prestamo[1]}")
                print(f"Fecha de vencimiento: {prestamo[3]}")
                print(f"Enviando correo al usuario {user[0]}...")
                send_email(f'El prestamo {prestamo[0]} ha vencido el {prestamo[3]}.', email_remitente, user[0], 'Prestamo Vencido')
                correos.append(user[0])

        else:
            print("No hay prestamos vencidos.")
        cursor.close()

        sleep(10)  # Esperar 60 segundos antes de volver a verificar

watch()