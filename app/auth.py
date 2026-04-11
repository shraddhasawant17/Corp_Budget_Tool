# ═══════════════════════════════════════════════════════════
# auth.py — Authentication ka Poora Brain
# ═══════════════════════════════════════════════════════════
#
# Yeh file 3 kaam karti hai:
#
# 1. PASSWORD HASHING
#    User ka password plain text mein kabhi store nahi karte
#    "Password123" → bcrypt → "$2b$12$xyz...abc" (random looking string)
#    Ek taraf ka process hai — hash se original password nahi nikal sakte
#    Login ke waqt: naya hash banao aur stored hash se compare karo
#
# 2. JWT TOKEN BANANA
#    JWT = JSON Web Token
#    Login ke baad user ko ek token milta hai
#    Har request ke saath yeh token bhejo — "mujhe pehchano"
#    Token ke andar: user_id, role, expiry time (encrypted)
#    Server har baar database hit nahi karta — token se hi verify hota hai
#
# 3. CURRENT USER IDENTIFY KARNA
#    Har protected route pe: token lao, decode karo, user kaun hai pata karo
#    Role bhi check karo — IT Head admin routes access nahi kar sakta
#
# JWT Structure (samajhne ke liye):
#   Header.Payload.Signature
#   eyJhbG... . eyJ1c2V... . SflKxw...
#   Header = algorithm info
#   Payload = actual data (user_id, role, expiry)
#   Signature = tamper-proof seal
# ═══════════════════════════════════════════════════════════

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
# jose = JavaScript Object Signing and Encryption — Python implementation
# JWT tokens banane aur verify karne ke liye

from passlib.context import CryptContext
# passlib = password hashing library
# CryptContext = multiple hashing schemes manage karna

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

# ── SECRET KEY ────────────────────────────────────────────
# Yeh key JWT signature banane ke liye use hoti hai
# Production mein yeh .env file mein honi chahiye — kabhi code mein hardcode mat karo
# Abhi prototype ke liye yahan rakh rahe hain
# Agar kisi ko yeh key mil jaaye to woh fake tokens bana sakta hai — isliye secret rakho
SECRET_KEY = "rbl-bank-it-budget-portal-secret-key-change-in-production-2024"

ALGORITHM = "HS256"
# HS256 = HMAC with SHA-256 — standard JWT algorithm
# Symmetric algorithm — sign aur verify dono ke liye same key

ACCESS_TOKEN_EXPIRE_MINUTES = 480
# Token kitni der valid rahega — 8 ghante (ek working day)
# Expire hone ke baad user ko dobara login karna hoga

# ── PASSWORD CONTEXT ──────────────────────────────────────
# CryptContext = password hashing ka handler
# schemes=["bcrypt"] = bcrypt algorithm use karo
# bcrypt kyun: deliberately slow hai — brute force attacks mushkil ho jaate hain
# deprecated="auto" = purane schemes automatically handle hote hain
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── OAUTH2 SCHEME ─────────────────────────────────────────
# OAuth2PasswordBearer = FastAPI ko batata hai ki token kahan milega
# tokenUrl = woh URL jahan token milta hai (login endpoint)
# Yeh automatically Authorization header check karta hai: "Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ═══════════════════════════════════════════════════════════
# PASSWORD FUNCTIONS
# ═══════════════════════════════════════════════════════════

def hash_password(plain_password: str) -> str:
    """
    Plain text password ko bcrypt hash mein convert karo
    
    Example:
        hash_password("MyPass123") → "$2b$12$LQv3c1yq..."
    
    Yeh hash database mein store hoga — never the original password
    """
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Login ke waqt: user ne jo password diya vs DB mein stored hash
    
    Example:
        verify_password("MyPass123", "$2b$12$LQv3c1yq...") → True
        verify_password("WrongPass", "$2b$12$LQv3c1yq...") → False
    
    Internally: plain password ko hash karke compare karta hai
    """
    return pwd_context.verify(plain_password, hashed_password)

# ═══════════════════════════════════════════════════════════
# JWT TOKEN FUNCTIONS
# ═══════════════════════════════════════════════════════════

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT token banao
    
    data = token ke andar kya store karna hai
    Example data: {"sub": "user@rblbank.com", "role": "it_head", "user_id": 5}
    
    Process:
    1. data ko copy karo
    2. expiry time add karo
    3. SECRET_KEY se sign karo
    4. Encoded string return karo
    """
    to_encode = data.copy()
    # .copy() isliye kyunki hum original dict modify nahi karna chahte

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    # "exp" = expiration — JWT standard claim
    # Token expire hone ke baad automatically invalid ho jaayega

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """
    JWT token decode karo — andar ka data nikalo
    
    Returns: {"sub": "email", "role": "...", "user_id": ...}
    Raises: JWTError agar token invalid ya expired hai
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload

# ═══════════════════════════════════════════════════════════
# CURRENT USER DEPENDENCY FUNCTIONS
# ═══════════════════════════════════════════════════════════
# FastAPI mein Dependencies = reusable functions jo automatically inject hoti hain
# Jab bhi koi protected route call hoga, yeh functions automatically chalenge
# Sochho jaise middleware but route-specific

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Har protected route pe yeh function chalega
    
    1. Request se JWT token nikalo (Authorization header se)
    2. Token decode karo
    3. Email/ID se DB mein user dhundo
    4. User object return karo — route function ko milega
    
    Agar kuch bhi galat hua — 401 Unauthorized error dega
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials. Please login again.",
        headers={"WWW-Authenticate": "Bearer"},
        # WWW-Authenticate header browser ko batata hai ki Bearer token chahiye
    )

    try:
        payload = decode_token(token)
        email: str = payload.get("sub")
        # "sub" = subject — JWT standard mein user identifier yahan store hota hai
        if email is None:
            raise credentials_exception
    except JWTError:
        # JWTError = token invalid, tampered, ya expired
        raise credentials_exception

    # DB se user nikalo
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account inactive. Please contact admin."
        )

    return user

# ── ROLE-BASED DEPENDENCY FUNCTIONS ──────────────────────
# Yeh functions specific roles ke liye hain
# IT Head route pe agar Admin aane ki koshish kare to 403 milega

async def require_it_head(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """Sirf IT Head access kar sakta hai"""
    if current_user.role != models.UserRole.IT_HEAD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. IT Head role required."
        )
    return current_user

async def require_admin(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """Sirf Admin (CA) access kar sakta hai"""
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required."
        )
    return current_user

async def require_super_admin(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """Sirf Super Admin (CEO) access kar sakta hai"""
    if current_user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Super Admin role required."
        )
    return current_user

async def require_admin_or_super_admin(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """Admin ya Super Admin — dono access kar sakte hain"""
    if current_user.role not in [models.UserRole.ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin or Super Admin role required."
        )
    return current_user

async def require_any_authenticated(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """Koi bhi logged in user — sirf authentication check"""
    # get_current_user ne pehle se hi authentication check kar liya
    # Yeh function explicit hai — code readable rehta hai
    return current_user

# ═══════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════

def generate_budget_key(db: Session, fy_year: str = "26") -> str:
    """
    Auto-generate unique budget key
    Format: RBL/IT/26/001, RBL/IT/26/002, ...
    
    Process:
    1. DB mein current FY ki last entry dhundo
    2. Last sequence number nikalo
    3. +1 karke nayi key banao
    """
    # Current FY ki prefix
    prefix = f"RBL/IT/{fy_year}/"

    # DB mein is prefix wali entries count karo
    count = db.query(models.BudgetLine).filter(
        models.BudgetLine.budget_key_current.like(f"{prefix}%")
    ).count()
    # .like() = SQL LIKE query — prefix se shuru hone wali entries

    # Nayi sequence number — 3 digits ke saath (001, 002, ...)
    sequence = str(count + 1).zfill(3)
    # .zfill(3) = "1" → "001", "12" → "012", "100" → "100"

    return f"{prefix}{sequence}"
    # Returns: "RBL/IT/26/001"
