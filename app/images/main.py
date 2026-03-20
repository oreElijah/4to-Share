from imagekitio import AsyncImageKit
from settings.config import GlobalConfig as Config

def get_imagekit_client():
    imagekit = AsyncImageKit(
        private_key=Config.IMAGEKIT_PRIVATE_KEY
    )

    return imagekit

imagekit = get_imagekit_client()