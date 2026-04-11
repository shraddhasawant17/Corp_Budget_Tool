# ═══════════════════════════════════════════════════════════
# database.py — Database Connection aur Session Management
# ═══════════════════════════════════════════════════════════
#
# Yeh file kya karti hai:
#   1. SQLite database file create karti hai (rbl_budget.db)
#   2. SQLAlchemy engine banati hai (engine = Python aur DB ke beech ka driver)
#   3. Session factory banati hai (har request ke liye ek DB session milega)
#   4. Base class deti hai jisse saare models inherit karenge
#
# SQLAlchemy kya hai:
#   Seedha SQL likhne ki jagah Python objects use karte hain.
#   Example: User(...) likhoge to automatically INSERT query chalegi.
#   Isko ORM kehte hain — Object Relational Mapper.
#
# SQLite kyun:
#   - Zero setup — koi server install nahi karna
#   - Ek .db file mein poora database
#   - Prototype ke liye perfect
#   - Baad mein PostgreSQL pe migrate karna aasaan hai
# ═══════════════════════════════════════════════════════════

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ── DATABASE URL ──────────────────────────────────────────
# SQLite ke liye format: sqlite:///./filename.db
# ./// matlab current folder mein file banao
# Jab pehli baar run hoga tab rbl_budget.db file automatically ban jayegi
# Koi SQL client install nahi karna — file hi database hai
DATABASE_URL = "sqlite:///./rbl_budget.db"

# ── ENGINE ────────────────────────────────────────────────
# Engine = Python aur Database ke beech ka connection driver
# Sochho jaise ki engine car chalata hai — without engine, car nahi chalti
# connect_args={"check_same_thread": False} — SQLite specific setting hai
# Kyun: SQLite by default ek hi thread allow karta hai
# FastAPI multiple threads use karta hai — isliye yeh setting zaroori hai
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# ── SESSION FACTORY ───────────────────────────────────────
# Session = ek temporary workspace jahan DB operations hote hain
# Jaise ek conversation — shuru hoti hai, kaam hota hai, band hoti hai
# autocommit=False matlab hum manually commit karenge (safer approach)
# autoflush=False matlab pending changes automatically DB mein nahi jayenge
# bind=engine matlab yeh session hamare engine se connected hai
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ── BASE CLASS ────────────────────────────────────────────
# Yeh Base class hai jisse saare database models inherit karenge
# Jab koi class Base inherit karegi, SQLAlchemy use ek DB table manega
# models.py mein dekho — class User(Base) likha hoga
Base = declarative_base()

# ── DATABASE SESSION DEPENDENCY ───────────────────────────
# Yeh ek generator function hai — FastAPI isko dependency injection ke liye use karta hai
# Har API request ke aane par:
#   1. Ek nayi DB session khulegi
#   2. Route function ko milegi
#   3. Kaam hone ke baad finally block mein close ho jayegi
# Yeh ensure karta hai ki koi bhi session leak na ho
# Chahe request success ho ya fail — session hamesha close hoga
def get_db():
    db = SessionLocal()
    try:
        yield db          # yield = function yahan pause ho jaata hai, db route ko milta hai
    finally:
        db.close()        # request khatam — session close
