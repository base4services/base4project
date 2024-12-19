import os
import asyncio
from email.mime.message import MIMEMessage

import aiosmtplib
from base4.utilities.db.async_redis import get_redis

from pydantic import BaseModel, EmailStr, NameEmail
from shared.services.sendmail.schemas.email_schema import EmailRequest

async def smtp_connect_and_send_message(message):

    SMTP_SERVER = os.getenv('SERVICES_SENDMAIL_SMTP_HOST')
    SMTP_PORT = os.getenv('SERVICES_SENDMAIL_SMTP_PORT')
    SMTP_USERNAME = os.getenv('SERVICES_SENDMAIL_SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SERVICES_SENDMAIL_SMTP_PASSWORD')

    if os.getenv('TEST_MODE', False)=='true' and not (os.getenv('SERVICES_SENDMAIL_ENABLED_IN_TEST_MODE', False)=='true'):
        return {'result': True, 'message': 'Email sent successfully in test mode', 'test': True}

    smtp = aiosmtplib.SMTP(hostname=SMTP_SERVER, port=int(SMTP_PORT),
                           username=SMTP_USERNAME, password=SMTP_PASSWORD)
    try:
        await smtp.connect()

        if type(message) == str:
            from email import message_from_string
            message = message_from_string(message)

        res = await smtp.send_message(message)
    except Exception as e:
        raise
    finally:
        await smtp.quit()

    response_txt = res[1]
    return {'result': '2.0.0 OK' in response_txt, 'message': response_txt, 'test': os.getenv('TEST_MODE', False)=='true'}


async def send_email(email_request: EmailRequest):
    mime_message = await email_request.mime()
    print(mime_message)
    res = await smtp_connect_and_send_message(message=mime_message)

async def send_next():
    async with get_redis() as redis:

        email = await redis.lpop('mailqueue')
        if not email:
            return False

    res = await smtp_connect_and_send_message(message=email['mime'])
    return res


async def enqueue_to_redis(email_request: EmailRequest):
    mime_message = await email_request.mime()
    async with get_redis() as redis:
        email = {
            'id': email_request.id,
            'mime': mime_message.as_string()
        }
        if os.getenv('TEST_MODE', False):
            email['to'] = email_request.to[0].email
            email['subject'] = email_request.subject
            email['body'] = email_request.body

        try:
            await redis.rpush('mailqueue', email)
        except Exception as e:
            raise

async def main():

    await enqueue_to_redis(EmailRequest(
        sender=NameEmail(name='Igor Jeremic',email='info@digitalcube.rs'),
        to=[NameEmail(name='Igor Jeremic',email='igor@digitalcube.rs')],
        subject='Test Subject',
        body='Test Body'))

    await send_next()


if __name__=='__main__':

    from  base4.utilities.files import env
    import dotenv

    dotenv.load_dotenv(env())

    asyncio.run(main())