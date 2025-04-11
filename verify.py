from twilio.rest import Client
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

TWILIO_ACCOUNT_SID = "ACab0920dfa265f2a7577f41f884eeb337"
TWILIO_AUTH_TOKEN = "081601d555a6f4ed6a0432e8cd5b419f"
TWILIO_PHONE_NUMBER = "+17173784639"


def send_mobile(phone_number, message=False, otp=False):
    body = '.\n\n'
    if message and not otp:
        body += message
        otp = None
    else:
        if otp:
            otp = str(random.randint(1000, 9999))
            body += message
            body += f'\nYour OTP is {otp}.'
        else:
            otp = str(random.randint(100000, 999999))
            body += f"The OTP for phone Verification of TMBL Online Bank System is {otp}."
    body += "\n\nPlease don't reply to this message."
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    phone_number = '+91' + phone_number
    try:
        client.messages.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            body=body
        )
        return str(otp)
    except Exception as e:
        print(f"Error sending OTP: {e}")
        return False


def send_email(to_email, subject=False, message=False):
    otp = False
    if message and subject:
        message = '\n\n' + message
        subject = subject
    else:
        subject = "TMBL Verification"
        otp = str(random.randint(1000, 9999))
        message = f"The OTP for mail Verification of TMBL Online Bank System is {otp}."

    message += "\n\nPlease don't reply to this mail."
    from_email = "online.bank.system.amrita@gmail.com"
    email_password = "hnlrusdbnbomteat"

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)  # For Gmail
        server.starttls()
        server.login(from_email, email_password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        if otp:
            return otp
    except Exception as e:
        print("Error sending email:", str(e))
        return False
