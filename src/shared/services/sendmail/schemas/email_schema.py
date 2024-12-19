import os
import uuid
from typing import Optional,  List, Dict, Any
from email_validator import validate_email as email_validator
from pydantic import BaseModel, EmailStr, NameEmail


from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import httpx
import base64
import re


def check_protocol(url):
    pattern = r'^(https?://|ftps?://)'
    return bool(re.match(pattern, url.strip().lower()))


async def fetch_and_encode(url: str) -> str:
    if check_protocol(url):
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.content
                # Get binary content and encode to base64
                # binary_content = response.content
                # base64_encoded = base64.b64encode(binary_content).decode('utf-8')
                # return base64_encoded
            else:
                raise Exception(f"Failed to fetch file: {response.status_code}")


class Attachment(BaseModel):
    filename: str
    content: Optional[str | None] = None  # base64 encoded content
    location: Optional[str | None] = None  # path to file
    cid: Optional[str | None] = None

    async def normalize(self):
        if self.location:
            self.content = await fetch_and_encode(self.location)
            self.location = None

    def __init__(self, **kwargs):

        content = kwargs.get('content')
        location = kwargs.get('location')

        if content and location:
            raise ValueError('Only one of content or location can be provided')

        if not content and not location:
            raise ValueError('Either content or location must be provided')

        if content:
            content = base64.b64decode(content)
            kwargs['content'] = content

        super().__init__(**kwargs)


class EmailRequest(BaseModel):
    sender: NameEmail
    reply_to: Optional[NameEmail | EmailStr | None] = None
    to: List[NameEmail]
    cc: Optional[List[NameEmail | EmailStr]] = None
    bcc: Optional[List[NameEmail | EmailStr]] = None
    subject: Optional[str | None] = None
    body: Optional[str | None] = None
    attachments: Optional[List[Attachment] | None] = None

    template: Optional[str | None] = None
    template_data: Optional[dict | None] = None

    id: Optional[uuid.UUID | None] = None

    async def mime(self):

        DEFAULT_EMAIL_RECEIVER_ADDRESS = os.getenv('DEFAULT_EMAIL_RECEIVER_ADDRESS', None)
        if os.getenv('TEST_MODE', False):
            if not DEFAULT_EMAIL_RECEIVER_ADDRESS:
                DEFAULT_EMAIL_RECEIVER_ADDRESS = 'igor.jeremic+emaili_testing@digitalcube.rs'

        message = MIMEMultipart()
        message['From'] = f"{self.sender.name} <{self.sender.email}>"

        if self.reply_to:
            if type(self.reply_to) == NameEmail:
                message['Reply-To'] = f"{self.reply_to.name} <{self.reply_to.email}>"
            else:
                message['Reply-To'] = self.reply_to

        if DEFAULT_EMAIL_RECEIVER_ADDRESS:
            message['To'] = DEFAULT_EMAIL_RECEIVER_ADDRESS
        else:
            message['To'] = ', '.join([f"{recipient.name} <{recipient.email}>" for recipient in self.to])

        if not DEFAULT_EMAIL_RECEIVER_ADDRESS:
            if self.cc:
                message['Cc'] = ', '.join([f"{recipient.name} <{recipient.email}>" for recipient in self.cc])
            if self.bcc:
                message['Bcc'] = ', '.join([f"{recipient.name} <{recipient.email}>" for recipient in self.bcc])

        if self.template:
            ...

        message["Subject"] = self.subject

        message.attach(MIMEText(self.body, 'html'))

        if self.attachments:
            for attachment in self.attachments:
                try:
                    await attachment.normalize()

                    if attachment.cid:
                        from email.mime.image import MIMEImage
                        from email import encoders

                        part = MIMEImage(attachment.content)
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', 'inline', filename=attachment.filename)
                        part.add_header("Content-ID", attachment.cid)

                        message.attach(part)

                    else:

                        from email.mime.base import MIMEBase
                        from email import encoders

                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment.content)
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename= {attachment.filename}",
                        )
                        if attachment.cid:
                            part.add_header(
                                "Content-ID",attachment.cid,
                            )

                        message.attach(part)
                except Exception as e:
                    raise ValueError(f'Error attaching file {attachment.filename}')

        return message

    def __init__(self, **kwargs):

        def eml(value: dict | str | NameEmail) -> NameEmail:
            if isinstance(value, dict):
                try:
                    email = email_validator(value['email'])
                    if 'name' in value:
                        email.display_name = value['name']
                    else:
                        email.display_name = email.ascii_email.split('@')[0].title()

                except Exception as e:
                    raise ValueError(f'Invalid email format')
                return NameEmail(name=email.display_name, email=email.ascii_email)

            if isinstance(value, str):
                try:
                    if '<' in value:
                        name, email = value.split('<')
                        email = email_validator(email.replace('>', ''))
                        email.display_name = name.strip().title()
                    else:
                        email = email_validator(value, test_environment=os.getenv('TEST_MODE', False))
                        email.display_name = email.ascii_email.split('@')[0].title()

                except Exception as e:
                    raise ValueError(f'Invalid email format')
                return NameEmail(name=email.display_name, email=email.ascii_email)

            if isinstance(value, NameEmail):
                return value
            raise ValueError(f'Invalid NameEmail format')

        def mk_list_of_named_emails(value: dict | str | NameEmail | list) -> List[NameEmail]:
            if not isinstance(value, list):
                value = [value]

            return [eml(x) for x in value]

        if 'sender' in kwargs:
            kwargs['sender'] = eml(kwargs['sender'])

        for key in ('to', 'cc', 'bcc'):
            if key in kwargs and kwargs[key]:
                kwargs[key] = mk_list_of_named_emails(kwargs[key])

        super().__init__(**kwargs)
