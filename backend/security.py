from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

# ================= CONFIG =================

SECRET_KEY = "SECRET123456"
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# ================= PASSWORD =================

def hash_password(password: str):
    return pwd_context.hash(password[:72])

def verify_password(
    plain_password,
    hashed_password
):
    return pwd_context.verify(
        plain_password[:72],
        hashed_password
    )

# ================= TOKEN =================

def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt
