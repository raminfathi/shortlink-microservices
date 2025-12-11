import jwt
import sys

# List of potential keys to test against the token
CANDIDATE_KEYS = [
    "final-fix-secret-key-12345",  # 1. The key currently in .env
    "fallback-secret",  # 2. The fallback defined in settings.py
    "mytestsecret123",  # 3. The previous key
    "jwt-fallback-secret-key",  # 4. Another common fallback
    "django-insecure-change-this-random-string-for-dev",  # 5. The Django SECRET_KEY
]
ALGORITHM = "HS256"


def debug_token(token_str):
    print(f"\n--- TOKEN DEBUGGER TOOL ---")

    try:
        # 1. Decode without verifying signature (to see the payload)
        unverified_header = jwt.get_unverified_header(token_str)
        print(f"Header: {unverified_header}")
        unverified_payload = jwt.decode(token_str, options={"verify_signature": False})
        print(f"Payload (Unverified): {unverified_payload}")
    except Exception as e:
        print(f"❌ Error decoding token structure: {e}")
        return

    print(f"\n--- BRUTE FORCE VERIFICATION ---")

    for key in CANDIDATE_KEYS:
        print(f"Testing key: '{key}' ... ", end="")
        try:
            # Try to verify with this specific key
            jwt.decode(token_str, key, algorithms=[ALGORITHM])
            print(f"✅ MATCH! The token was signed with this key.")
            return
        except jwt.InvalidSignatureError:
            print(f"❌ Failed (Signature mismatch)")
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n❌ CONCLUSION: None of the candidate keys matched. The key is something completely different.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_token.py <YOUR_TOKEN_HERE>")
    else:
        # The token might be passed with "Bearer " prefix, let's clean it
        raw_token = sys.argv[1].replace("Bearer ", "").strip()
        # Remove quotes if accidentally included
        raw_token = raw_token.replace('"', '').replace("'", "")
        debug_token(raw_token)