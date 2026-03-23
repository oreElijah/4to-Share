import httpx
from typing import Annotated
from pathlib import Path
from pydantic import NameEmail
from .processor import send_mail_task
from settings.config import Configs, get_config
from fastapi import Depends
from jinja2 import Environment, FileSystemLoader
from fastapi_mail import ConnectionConfig, FastMail, MessageType, MessageSchema
from fastapi_mail.errors import ConnectionErrors


def resolve_template_folder(base_dir: str) -> Path:
    configured = Path(base_dir)
    if configured.is_dir():
        return configured

    # Fallback for cloud deploys where local Windows paths don't exist.
    return Path(__file__).resolve().parent / "templates"

class MailService:
    def __init__(self, setting: Annotated[Configs, Depends(get_config)]):

        self.setting = setting

        TEMPLATE_FOLDER = resolve_template_folder(setting.BASE_DIR)

        self.api_key = self.setting.BREVO_API_KEY
        self.jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_FOLDER))

    async def send_mail(self, message):
        url = "https://api.brevo.com/v3/smtp/email"

        payload = {
            "sender": {
                "name": self.setting.MAIL_FROM_NAME,
                "email": self.setting.MAIL_FROM
            },
            "to": [
                {
                    "email": str(r.email),
                    "name": r.name
                } for r in message.recipients
            ],
            "subject": message.subject,
            "htmlContent": message.body
        }

        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
            "content-type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code >= 400:
            raise Exception(f"Brevo error: {response.text}")

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

        try:
            await self.send_mail(message=message)
        except Exception as e:
            print("Email failed:", e)

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

