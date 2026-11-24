import redis
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

redis_url = settings.BASE_REDIS_URL
redis_client = redis.from_url(f"{redis_url}/0", decode_responses=True)


class RedisCheckedJWTAuthentication(JWTAuthentication):
    """
    Extends SimpleJWT to verify that the incoming Access Token
    has not been blacklisted in Redis.
    """

    def get_validated_token(self, raw_token):
        # 1. Perform standard cryptographic signature and expiration check
        validated_token = super().get_validated_token(raw_token)

        # 2. Check if the token's unique ID (`jti`) is sitting in Redis:
        jti = validated_token.get("jti")
        if jti and redis_client.exists(f"blacklist:{jti}"):
            raise InvalidToken("This access token has been revoked by logout.")

        return validated_token
