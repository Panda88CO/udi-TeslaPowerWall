import requests
from time import sleep
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
import base64

import smtplib, ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
    PG_CLOUD_ONLY = True  
LOGGER = polyinterface.LOGGER


# You will need pip install svglib

# It goes to say this work takes effort so please use my referral to support my work
# https://2captcha.com?from=11874928 
# The link above allows you to create a acount with 2captcha which is what we use
# If you know me we can share API key, just reach out to me  thanks
# Appreciate donations to keep 2captcha going, anything helps

API_KEY = 'c510660acfb35bf6cb241038cd430cce'  # Your 2captcha API KEY
CAPTCHA_ENABLE = True

def getCaptcha(headers, cookies):  
    # Captcha is session based so use the same headers
    LOGGER.debug('Getting captcha')
    catpcha = requests.get('https://auth.tesla.com/captcha', headers=headers, cookies=cookies)

    # Save captch as .png image to send 2Captcha service locally
    file = open("captcha.svg", "wb")
    file.write(catpcha.content)
    file.close()

    drawing = svg2rlg("captcha.svg")
    renderPM.drawToFile(drawing, "captcha.png", fmt="PNG")
    return('captcha.png')


def solveCaptcha(captchaFile, captchaApiKey):

        # Encode image base 64
        with open(captchaFile, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read())

        # Now use the image file saved locally to post to captcha service and wait for response
        # here we post site key to 2captcha to get captcha ID (and we parse it here too)
        current_url = "http://2captcha.com/in.php"

        data = {
            "key": captchaApiKey,
            "method": "base64",
            "body": encoded_string,
            "regsense": 1,
            "textinstructions": "text",        
        }
           
        #files = open(captchaFile, 'rb')
        resp = requests.post(current_url, data=data)
        if 'OK' in resp.text:
            captcha_id = resp.text.split('|',1)[1]
        else:
            LOGGER.error('error posting captcha')
        # Change data to be getting the answer from 2captcha
        data = {
            "key": API_KEY,
            "action": "get",
            "id": captcha_id
        }
        answer_url = "http://2captcha.com/res.php"
        resp = requests.get(answer_url, params=data)

        captcha_answer = resp.text
        while 'CAPCHA_NOT_READY' in captcha_answer:
            sleep(5)
            
            resp = requests.get(answer_url, params=data)
            captcha_answer = resp.text
            #print (captcha_answer)
        
        if 'OK' in captcha_answer:
            captcha_answer = captcha_answer.split('|',1)[1]
        else:
            LOGGER.error('error getting captcha answer')
        LOGGER.info('captcha = '+ captcha_answer)

        return (captcha_answer)
    # if captcha not enabled just return empty string

def sendEmailCaptcha(captchaFile, email):

    subject = "Please solve captcha image"
    body = "This is an email with captcha image from TeslaPowerWall login.  Input data to polisy"
    sender_email = "isy_powerwall@outlook.com"
    receiver_email = email
    password = "isy123ISY!@#"

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    #message["Bcc"] = receiver_email  # Recommended for mass emails

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    filename = captchaFile  # In same directory as script

    # Open PDF file in binary mode
    with open(filename, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to send by email    
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}",
    )

    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    # Log in to server using secure context and send email


    context = ssl.create_default_context()
    with smtplib.SMTP("smtp-mail.outlook.com", 587) as smtp:
        smtp.ehlo()  # Say EHLO to server
        smtp.starttls(context=context)  # Puts the connection in TLS mode.
        smtp.ehlo()
        smtp.login(sender_email, password)
        smtp.sendmail(sender_email, receiver_email, text)
        LOGGER.info('captcha email sent')