import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .config import settings

security = HTTPBearer()


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Security(security)) -> int:
    token = credentials.credentials
    raw_key = settings.JWT_SECRET_KEY
    clean_key = raw_key.strip()


    test_token = jwt.encode(
        {"user_id": 7},
        clean_key,
        algorithm=settings.JWT_ALGORITHM
    )
    print(f"DEBUG: Core-API Generated Token Signature: {test_token.split('.')[-1]}")
    raw_key = settings.JWT_SECRET_KEY
    clean_key = raw_key.strip()

    print(f"\n--- DEEP DEBUG AUTH ---")
    print(f"Token: {token[:10]}...")
    print(f"Raw Key (repr): {repr(raw_key)}")
    print(f"Clean Key (repr): {repr(clean_key)}")

    try:
        payload = jwt.decode(
            token,
            clean_key,
            algorithms=[settings.JWT_ALGORITHM]
        )

        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="User ID missing")

        return user_id

    except jwt.InvalidTokenError as e:
        print(f"ERROR: Verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )