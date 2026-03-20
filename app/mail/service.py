import os
from typing import List, Annotated
from pathlib import Path
from pydantic import NameEmail
from .processor import send_mail_task
from settings.config import Configs, get_config
from fastapi import Depends
from jinja2 import Environment, FileSystemLoader
from fastapi_mail import ConnectionConfig, FastMail, MessageType, MessageSchema

class MailService:
    def __init__(self, setting: Annotated[Configs, Depends(get_config)]):

        self.setting = setting

        TEMPLATE_FOLDER = Path(setting.BASE_DIR)

        self.config = ConnectionConfig(
    MAIL_USERNAME = self.setting.MAIL_USERNAME,
    MAIL_PASSWORD = (self.setting.MAIL_PASSWORD), # type: ignore
    MAIL_FROM = self.setting.MAIL_FROM,
    MAIL_FROM_NAME = self.setting.MAIL_FROM_NAME,
    MAIL_PORT = self.setting.MAIL_PORT,
    MAIL_SERVER = self.setting.MAIL_SERVER,
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True,
    TEMPLATE_FOLDER=TEMPLATE_FOLDER
        )

        self.client = FastMail (
            config=self.config
        )

        self.jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_FOLDER))

    async def send_mail(self, message: MessageSchema) -> None:
        if False:
            message_dict = message.model_dump()
            message_dict["subtype"] = message_dict["subtype"].value
            message_dict['multipart_subtype'] = message_dict['multipart_subtype'].value

            config_dict = self.config.model_dump()
            config_dict["MAIL_PASSWORD"] = config_dict["MAIL_PASSWORD"].get_secret_value()
            config_dict["TEMPLATE_FOLDER"] = config_dict["TEMPLATE_FOLDER"].as_posix()
    
            send_mail_task.apply_async(kwargs={ 'message_dict': message_dict, 'config_dict': config_dict })
        else:
            await self.client.send_message(message=message)


    async def send_password_reset(self, first_name: str, email: str, token: str) -> None:
        password_reset_template = self.jinja_env.get_template("password_reset.j2")

        password_reset_link = f"{self.setting.FRONTEND_URL}/?reset_token={token}"

        body = password_reset_template.render(header="Password Reset", name=f"{first_name}", password_reset_link=password_reset_link)

        message = MessageSchema(
            recipients=[NameEmail(name=first_name, email=email)],
            body=body,
            subject="Password Reset",
            from_email=self.setting.MAIL_FROM,
            from_name=self.setting.MAIL_FROM_NAME,
            subtype=MessageType.html
        )

        await self.send_mail(message=message)

    async def send_verify_mail(self, *, first_name: str, email: str, verify_token: str) -> None:
        verify_template = self.jinja_env.get_template("verify_mail.j2")

        body = verify_template.render(header="Verify Email", name=f"{first_name}", verification_link=f"{self.setting.DOMAIN}/v1/auth/verify/{verify_token}")

        message = MessageSchema(
            recipients=[NameEmail(name=first_name, email=email)],
            body=body,
            subject="Verify Email",
            from_email=self.setting.MAIL_FROM,
            from_name=self.setting.MAIL_FROM_NAME,
            subtype=MessageType.html
        )

        await self.send_mail(message=message)

    # def create_message(recipients: List[str], subject: str, body: str):
    #     message = MessageSchema(
    #         recipients=recipients,
    #         subject=subject,
    #         body=body,
    #         subtype=MessageType.html
    #     )
    #     return message

