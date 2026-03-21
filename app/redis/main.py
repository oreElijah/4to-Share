from upstash_redis import Redis
from settings.config import GlobalConfig as Config
import json

token_blocklist = Redis(url=Config.UPSTASH_REDIS_REST_URL, token=Config.UPSTASH_REDIS_REST_TOKEN) # type: ignore

def add_jti_to_blocklist(jti: str):
    token_blocklist.set(
        key=jti,
         value= "",
         ex= Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    
def jti_in_blocklist(jti: str) -> bool:
    msg = token_blocklist.get(key=jti)
    return msg is not None
