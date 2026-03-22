# bot/utils/helpers.py
# Helper functions — unique codes etc.

import random
import string


def generate_unique_code(length: int = 8) -> str:
    """
    Random unique code generate karo.
    Example: xK9mP2qR
    """
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


def generate_referral_code(telegram_id: int) -> str:
    """
    User ke liye referral code banao.
    Example: REF_12345678
    """
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"REF{telegram_id}{suffix}"
