import asyncio
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema


async def send_mail_task(message_dict: dict[str, str], config_dict: dict[str, str]) -> None:
    mail_client = FastMail(ConnectionConfig(**config_dict)) # type: ignore
    message = MessageSchema(**message_dict) # type: ignore

    await mail_client.send_message(message)