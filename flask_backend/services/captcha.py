import hashlib
import hmac
import random
import time
from flask import current_app


def make_captcha():
    """
    Generate a 6-digit Security OTP verification code and an HMAC-SHA256 signature token.
    Valid for 10 minutes (600 seconds).
    """
    otp = f"{random.randint(100000, 999999)}"
    exp = int(time.time()) + 600
    raw = f"{otp}:{exp}"
    secret = current_app.config["SECRET_KEY"].encode("utf-8")
    sig = hmac.new(secret, raw.encode("utf-8"), hashlib.sha256).hexdigest()
    token = f"{otp}:{exp}:{sig}"
    return {
        "otp": otp,
        "code": otp,
        "question": otp,
        "token": token,
        "expires_in": 600,
    }


def validate_captcha(token, user_answer):
    """
    Validate the OTP verification token and user answer.
    Ignores spaces and dashes in input.
    """
    if not token or user_answer is None:
        return False
    try:
        parts = str(token).split(":")
        if len(parts) != 3:
            return False
        expected_ans, exp_str, sig = parts
        if time.time() > int(exp_str):
            return False
        raw = f"{expected_ans}:{exp_str}"
        secret = current_app.config["SECRET_KEY"].encode("utf-8")
        valid_sig = hmac.new(secret, raw.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, valid_sig):
            return False
        clean_user = str(user_answer).replace(" ", "").replace("-", "").strip()
        clean_expected = str(expected_ans).replace(" ", "").replace("-", "").strip()
        return clean_user == clean_expected
    except Exception:
        return False
