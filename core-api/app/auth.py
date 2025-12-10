import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .config import settings

# This dependency automatically checks for "Authorization: Bearer <token>" header
security = HTTPBearer()


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Security(security)) -> int:
    """
    Validates the JWT token and returns the user ID (stored in 'user_id' claim).
    This function acts as a FastAPI dependency.
    """

    token = credentials.credentials

    try:
        # Decode the token using the shared secret key
        # SimpleJWT uses HS256 by default for signing
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # SimpleJWT stores the user ID in the 'user_id' claim
        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: user_id missing",
            )

        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


