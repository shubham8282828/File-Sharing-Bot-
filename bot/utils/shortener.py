# bot/utils/shortener.py
# URL shortener integration

import requests
import logging
from config import SHORTENER_API_KEY, SHORTENER_DOMAIN

logger = logging.getLogger(__name__)


def shorten_url(long_url: str) -> str:
    """
    URL ko shorten karo shortener API se.
    User yeh link complete karega → token milega.
    """
    if not SHORTENER_API_KEY:
        # API key nahi hai — original URL return karo
        logger.warning("⚠️ SHORTENER_API_KEY nahi hai!")
        return long_url

    try:
        api_url = (
            f"{SHORTENER_DOMAIN}/api"
            f"?api={SHORTENER_API_KEY}"
            f"&url={long_url}"
        )
        response = requests.get(api_url, timeout=10)
        data = response.json()

        if data.get("status") == "success":
            short_url = data.get("shortenedUrl", long_url)
            logger.info(f"✅ URL shortened: {short_url}")
            return short_url
        else:
            logger.error(f"❌ Shortener error: {data}")
            return long_url

    except Exception as e:
        logger.error(f"❌ Shortener exception: {e}")
        return long_url
