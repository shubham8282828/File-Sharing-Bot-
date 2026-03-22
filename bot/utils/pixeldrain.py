# bot/utils/pixeldrain.py
# Pixeldrain pe file upload karne ka utility

import requests
import logging
from config import PIXELDRAIN_API_KEY

logger = logging.getLogger(__name__)


def upload_to_pixeldrain(file_path: str, file_name: str) -> dict:
    """
    File ko Pixeldrain pe upload karo.
    
    Returns:
        dict: {
            "success": True/False,
            "file_id": "abc123",   ← Yeh save karenge
            "error": "..."         ← Agar error ho
        }
    """
    try:
        url = "https://pixeldrain.com/api/file"

        # File open karo aur upload karo
        with open(file_path, "rb") as f:
            response = requests.post(
                url,
                auth=("", PIXELDRAIN_API_KEY),  # Pixeldrain auth format
                files={"file": (file_name, f)},
                timeout=300  # 5 min timeout — badi files ke liye
            )

        # Response check karo
        if response.status_code == 201:
            data = response.json()
            file_id = data.get("id")
            logger.info(f"✅ Pixeldrain upload success: {file_id}")
            return {"success": True, "file_id": file_id}
        else:
            error = response.json().get("message", "Unknown error")
            logger.error(f"❌ Pixeldrain upload failed: {error}")
            return {"success": False, "error": error}

    except Exception as e:
        logger.error(f"❌ Pixeldrain exception: {e}")
        return {"success": False, "error": str(e)}


def check_pixeldrain_link(file_id: str) -> bool:
    """
    Check karo ki Pixeldrain file abhi bhi exist karti hai ya nahi.
    Yeh Step 11 (auto re-upload) mein use hoga.
    """
    try:
        url = f"https://pixeldrain.com/api/file/{file_id}/info"
        response = requests.get(
            url,
            auth=("", PIXELDRAIN_API_KEY),
            timeout=10
        )
        return response.status_code == 200
    except:
        return False
