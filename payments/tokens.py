from django.core.signing import TimestampSigner

UNDERPAYMENT_TOKEN_SALT = "payments.resolve_underpayment.v1"
UNDERPAYMENT_TOKEN_MAX_AGE = 7 * 24 * 60 * 60


def make_underpayment_token(payment_id: str, user_id: str) -> str:
    signer = TimestampSigner(salt=UNDERPAYMENT_TOKEN_SALT)
    return signer.sign_object({"pid": str(payment_id), "uid": str(user_id)})


def verify_underpayment_token(token: str) -> tuple[str, str]:

    signer = TimestampSigner(salt=UNDERPAYMENT_TOKEN_SALT)
    data = signer.unsign_object(token, max_age=UNDERPAYMENT_TOKEN_MAX_AGE)
    return data["pid"], data["uid"]
