import redis.asyncio as redis
from settings.config import GlobalConfig as Config
import json

token_blocklist = redis.from_url(
    Config.REDIS_URL
)

async def add_jti_to_blocklist(jti: str) -> None:
    await token_blocklist.set(
        name=jti,
         value= "",
         ex= Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    
async def jti_in_blocklist(jti: str) -> bool:
    msg = await token_blocklist.get(name=jti)
    return msg is not None
