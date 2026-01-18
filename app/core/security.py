import base64
import json
import time
from typing import Any, Dict
from urllib.request import urlopen

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec as cryptography_ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicNumbers
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

bearer_scheme = HTTPBearer()

# Simple in-memory JWKS cache
JWKS_CACHE: Dict[str, Any] = {"keys": None, "fetched_at": 0}
JWKS_TTL = 300  # seconds


def _fetch_jwks() -> Dict[str, Any]:
    now = time.time()
    if JWKS_CACHE["keys"] and now - JWKS_CACHE["fetched_at"] < JWKS_TTL:
        return JWKS_CACHE["keys"]

    jwks_url = settings.supabase_url.rstrip("/") + "/.well-known/jwks.json"
    with urlopen(jwks_url, timeout=5) as resp:
        data = resp.read()
        jwks = json.loads(data)
        JWKS_CACHE["keys"] = jwks
        JWKS_CACHE["fetched_at"] = now
        print("Fetched JWKS from:", jwks_url)
        return jwks


def _find_jwk(kid: str) -> Dict[str, Any]:
    jwks = _fetch_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    raise KeyError(f"JWK with kid={kid} not found")


def _base64url_to_int(val: str) -> int:
    # Add padding if necessary
    val_padded = val + "=" * (-len(val) % 4)
    data = base64.urlsafe_b64decode(val_padded)
    return int.from_bytes(data, "big")


def _jwk_to_pem(jwk: Dict[str, Any]) -> bytes:
    kty = jwk.get("kty")
    if kty == "RSA":
        n = _base64url_to_int(jwk["n"])
        e = _base64url_to_int(jwk["e"])
        pub_numbers = RSAPublicNumbers(e, n)
        pub_key = pub_numbers.public_key(default_backend())
        pem = pub_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pem
    elif kty == "EC":
        # Support P-256 curve (ES256)
        x = _base64url_to_int(jwk["x"])
        y = _base64url_to_int(jwk["y"])
        curve_name = jwk.get("crv")
        if curve_name != "P-256":
            raise ValueError(f"Unsupported EC curve: {curve_name}")
        curve = cryptography_ec.SECP256R1()
        pub_numbers = EllipticCurvePublicNumbers(x, y, curve)
        pub_key = pub_numbers.public_key(default_backend())
        pem = pub_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pem
    else:
        raise ValueError(f"Unsupported JWK kty: {kty}")


def get_current_user(token: str = Depends(bearer_scheme)):
    payload = None

    # First, try HS256 verification with the Supabase secret.
    try:
        payload = jwt.decode(
            token=token.credentials,
            key=settings.supabase_secret_key,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        print("JWT Payload (verified HS256):", payload)
    except JWTError as hs_err:
        print(f"HS256 verification failed or token not HS256: {hs_err}")

        # If HS256 verification failed, attempt JWKS-based verification by iterating keys.
        try:
            jwks = _fetch_jwks()
        except Exception as e:
            print(f"Failed to fetch JWKS: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Supabase token",
            )

        last_exc = None
        for jwk in jwks.get("keys", []):
            try:
                pem = _jwk_to_pem(jwk)
            except Exception as e:
                # Skip keys we can't convert
                last_exc = e
                continue

            try:
                # Let the library validate the token signature and algorithm.
                payload = jwt.decode(
                    token=token.credentials,
                    key=pem,
                    algorithms=["RS256", "ES256"],
                    options={"verify_aud": False},
                )
                print("JWT Payload (verified via JWKS):", payload)
                break
            except JWTError as e:
                last_exc = e
                continue

        if payload is None:
            print(f"JWT verification via JWKS failed: {last_exc}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Supabase token",
            )

    # Try to get role from different possible locations in the payload
    role = (
        payload.get("user_metadata", {}).get("role")
        or payload.get("app_metadata", {}).get("role")
        or payload.get("role")
        or "patient"
    )

    return {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "role": role,
    }


def require_role(*roles):
    def wrapper(user=Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return user

    return wrapper


require_admin = require_role("admin")
