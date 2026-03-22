import logging
import asyncio
from typing import Annotated
from pathlib import Path
import httpx
from pydantic import NameEmail
from .processor import send_mail_task
from settings.config import Configs, get_config
from fastapi import Depends
from jinja2 import Environment, FileSystemLoader
from fastapi_mail import ConnectionConfig, FastMail, MessageType, MessageSchema
from fastapi_mail.errors import ConnectionErrors


logger = logging.getLogger(__name__)


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

        self.config = ConnectionConfig(
    MAIL_USERNAME = self.setting.MAIL_USERNAME,
    MAIL_PASSWORD = (self.setting.MAIL_PASSWORD), # type: ignore
    MAIL_FROM = self.setting.MAIL_FROM,
    MAIL_FROM_NAME = self.setting.MAIL_FROM_NAME,
    MAIL_PORT = self.setting.MAIL_PORT,
    MAIL_SERVER = self.setting.MAIL_SERVER,
    MAIL_STARTTLS = self.setting.MAIL_STARTTLS,
    MAIL_SSL_TLS = self.setting.MAIL_SSL_TLS,
    TIMEOUT = self.setting.MAIL_TIMEOUT,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True,
    TEMPLATE_FOLDER=TEMPLATE_FOLDER
        )

        self.client = FastMail (
            config=self.config
        )

        self.jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_FOLDER))

    async def _send_with_smtp(self, message: MessageSchema) -> None:
        attempts = max(1, self.setting.MAIL_MAX_RETRIES + 1)
        for attempt in range(1, attempts + 1):
            try:
                await self.client.send_message(message=message)
                return
            except Exception:
                if attempt < attempts:
                    await asyncio.sleep(self.setting.MAIL_RETRY_DELAY_SECONDS)
                    continue
                raise

    async def _send_with_resend(self, message: MessageSchema) -> None:
        if not self.setting.RESEND_API_KEY:
            raise RuntimeError("RESEND_API_KEY is not configured")

        recipients = [str(recipient) for recipient in message.recipients]
        payload = {
            "from": f"{self.setting.MAIL_FROM_NAME} <{self.setting.MAIL_FROM}>",
            "to": recipients,
            "subject": message.subject,
            "html": message.body,
        }
        headers = {
            "Authorization": f"Bearer {self.setting.RESEND_API_KEY}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.setting.MAIL_TIMEOUT) as client:
            response = await client.post(self.setting.RESEND_API_URL, json=payload, headers=headers)
            response.raise_for_status()

    async def send_mail(self, message: MessageSchema) -> None:
        if not self.setting.MAIL_ENABLED:
            logger.info("Mail sending disabled (MAIL_ENABLED=false).")
            return

        if False:
            message_dict = message.model_dump()
            message_dict["subtype"] = message_dict["subtype"].value
            message_dict['multipart_subtype'] = message_dict['multipart_subtype'].value

            config_dict = self.config.model_dump()
            config_dict["MAIL_PASSWORD"] = config_dict["MAIL_PASSWORD"].get_secret_value()
            config_dict["TEMPLATE_FOLDER"] = config_dict["TEMPLATE_FOLDER"].as_posix()
    
            send_mail_task.apply_async(kwargs={ 'message_dict': message_dict, 'config_dict': config_dict })
        else:
            try:
                await self._send_with_smtp(message=message)
            except ConnectionErrors as exc:
                logger.warning("SMTP connection failed: %s", exc)
                if self.setting.RESEND_API_KEY:
                    try:
                        await self._send_with_resend(message=message)
                        logger.info("Email sent via Resend fallback.")
                        return
                    except Exception as resend_exc:
                        if self.setting.MAIL_FAIL_SILENTLY:
                            logger.warning("Resend fallback failed: %s", resend_exc)
                            return
                        logger.exception("Resend fallback failed.")
                        raise

                if self.setting.MAIL_FAIL_SILENTLY:
                    return
                raise
            except Exception as exc:
                if self.setting.MAIL_FAIL_SILENTLY:
                    logger.warning("Unexpected mail error: %s", exc)
                    return
                logger.exception("Unexpected error while sending email.")
                raise


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

