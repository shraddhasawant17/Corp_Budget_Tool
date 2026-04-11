# ═══════════════════════════════════════════════════════════
# models.py — Database Tables ka Structure (Schema)
# ═══════════════════════════════════════════════════════════
#
# Model kya hota hai:
#   Ek Python class jo ek database table represent karti hai.
#   Har class = ek table
#   Har class attribute = ek column
#
# Yahan 4 tables hain:
#   1. User        → Login karne wale log (IT Head, Admin, CEO)
#   2. BudgetLine  → Har ek budget entry (Oracle license, AWS etc.)
#   3. Approval    → Kaun ne kya action liya (approve/reject + comment)
#   4. Dummy1      → Future use (placeholder)
#   5. Dummy2      → Future use (placeholder)
#
# Relationships:
#   User → BudgetLine  : Ek user kai budget lines submit kar sakta hai (One to Many)
#   BudgetLine → Approval : Ek budget line pe kai actions ho sakte hain (One to Many)
# ═══════════════════════════════════════════════════════════

from sqlalchemy import (
    Column, Integer, String, Float,
    Boolean, DateTime, Text, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

# ── ENUMS ─────────────────────────────────────────────────
# Enum = predefined fixed values — column mein sirf yahi values allowed hain
# Kyun enum use karo: typo se bachao, consistency ensure karo
# Agar role="adminn" likha to DB reject karega — safety net hai yeh

class UserRole(str, enum.Enum):
    # str inherit kiya hai taaki JSON serialization easy ho
    IT_HEAD     = "it_head"       # Budget fill karta hai
    ADMIN       = "admin"         # CA — verify karta hai
    SUPER_ADMIN = "super_admin"   # CEO — final approve

class BudgetStatus(str, enum.Enum):
    DRAFT              = "draft"               # IT Head ne save kiya, submit nahi
    SUBMITTED          = "submitted"           # IT Head ne submit kiya
    ADMIN_APPROVED     = "admin_approved"      # CA ne approve kiya, CEO ke paas gaya
    REJECTED_BY_ADMIN  = "rejected_by_admin"   # CA ne reject kiya
    FINAL_APPROVED     = "final_approved"      # CEO ne final approve kiya
    REJECTED_BY_CEO    = "rejected_by_ceo"     # CEO ne reject kiya

class ExpenseSubType(str, enum.Enum):
    OPEX  = "opex"   # Recurring: monthly/annual charges
    CAPEX = "capex"  # One-time: hardware, new software purchase

class OldNew(str, enum.Enum):
    OLD = "old"   # Pehle se chal raha hai
    NEW = "new"   # Pehli baar budget maang rahe hain

class ApprovalAction(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    FORWARDED = "forwarded"  # Admin ne CEO ko forward kiya

# ═══════════════════════════════════════════════════════════
# TABLE 1 — USERS
# ═══════════════════════════════════════════════════════════
class User(Base):
    __tablename__ = "users"
    # __tablename__ = SQLite mein table ka actual naam

    # ── Primary Key ──
    # Integer primary key — auto-increment hota hai SQLite mein
    # Matlab pehla user id=1, doosra id=2 — khud increment hoga
    id = Column(Integer, primary_key=True, index=True)

    # ── Basic Info ──
    full_name  = Column(String(100), nullable=False)
    # nullable=False matlab yeh field required hai — empty nahi chhod sakte

    email      = Column(String(150), unique=True, nullable=False, index=True)
    # unique=True matlab ek email sirf ek user ke paas ho sakti hai
    # index=True matlab is column pe search fast hogi (DB index banata hai)

    password   = Column(String(255), nullable=False)
    # Yahan hashed password store hoga — kabhi plain text nahi
    # passlib library se hash karenge — auth.py mein dekho

    # ── Role ──
    role = Column(Enum(UserRole), nullable=False, default=UserRole.IT_HEAD)
    # Enum(UserRole) matlab sirf UserRole ke defined values allowed hain

    # ── IT Head Specific ──
    # Yeh fields sirf IT Head ke liye relevant hain
    # Admin/CEO ke liye None/null rahenge — that's okay
    department = Column(String(100), nullable=True)
    # Konsa department: Retail Banking, Digital Banking etc.

    spoc_email = Column(String(150), nullable=True)
    # SPOC = Single Point of Contact — IT Head ka contact person

    cost_code  = Column(String(50), nullable=True)
    # Har department ka fixed cost code — auto-fill ke liye

    # ── Account Status ──
    is_active  = Column(Boolean, default=True)
    # False karo to user login nahi kar payega — soft delete

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # server_default=func.now() matlab DB server apna timestamp deta hai
    # Python side se manually datetime nahi dena — more reliable

    # ── Relationships ──
    # SQLAlchemy ko batao ki User aur BudgetLine related hain
    # back_populates = dono side se relationship access kar sako
    # user.budget_lines → us user ki saari lines
    # budget_line.submitted_by_user → kaun ne submit kiya
    budget_lines = relationship("BudgetLine", back_populates="submitted_by_user")
    approvals    = relationship("Approval", back_populates="action_by_user")

    def __repr__(self):
        # Debugging ke liye — print(user) karo to yeh dikhega
        return f"<User id={self.id} email={self.email} role={self.role}>"

# ═══════════════════════════════════════════════════════════
# TABLE 2 — BUDGET LINES
# ═══════════════════════════════════════════════════════════
class BudgetLine(Base):
    __tablename__ = "budget_lines"

    id = Column(Integer, primary_key=True, index=True)

    # ── Identity Fields ──
    budget_key_current  = Column(String(50), unique=True, nullable=False)
    # Auto-generate karenge: RBL/IT/26/001 format mein
    # unique=True kyunki har budget line ka unique ID hona chahiye

    budget_key_previous = Column(String(50), nullable=True)
    # Sirf OLD entries ke liye — NEW entries ke liye None rahega

    old_new = Column(Enum(OldNew), nullable=False)

    # ── Ownership Fields ──
    business_name = Column(String(100), nullable=False)
    # Retail Banking, Corporate Banking etc.

    cost_code     = Column(String(50), nullable=False)
    # User ke profile se auto-fill hoga

    submitted_by  = Column(Integer, ForeignKey("users.id"), nullable=False)
    # ForeignKey("users.id") = yeh column users table ke id se linked hai
    # Matlab har budget line kisi na kisi user ne submit ki hai
    # Agar user delete ho to kya hoga? Isliye ondelete handle karna padega baad mein

    # ── Expense Classification ──
    expense_sub_type    = Column(Enum(ExpenseSubType), nullable=False)
    # OPEX ya CAPEX — yahi se dashboard cards calculate honge

    description         = Column(String(200), nullable=False)
    # Short one-line description

    expense_description = Column(Text, nullable=True)
    # Detailed description — Text type = unlimited length
    # String vs Text: String = fixed length limit, Text = unlimited

    application_platform = Column(String(100), nullable=True)
    # Oracle, AWS, SAP, Finacle etc.

    vendor_name          = Column(String(100), nullable=True)
    resource_count       = Column(Integer, nullable=True)

    # ── Money Fields ──
    # Float use kiya hai amounts ke liye
    # Production mein Numeric(precision, scale) use karte hain — more accurate
    # Abhi Float prototype ke liye theek hai

    budget_amt_current_fy   = Column(Float, nullable=False)
    # Final Budget FY 25-26 (A)

    projected_consumption   = Column(Float, nullable=False)
    # Projected Consumption FY 25-26 (B)

    budget_amt_next_fy      = Column(Float, nullable=False)
    # Budget Requested FY 26-27 (C)

    # ── Calculated Fields ──
    # Yeh DB mein store karenge taaki reports mein fast query ho sake
    # Frontend pe bhi calculate honge (real-time) lekin DB mein bhi rakho
    diff_a_minus_b          = Column(Float, nullable=True)   # A - B
    diff_c_minus_b          = Column(Float, nullable=True)   # C - B
    diff_c_minus_a          = Column(Float, nullable=True)   # C - A

    # ── Justification ──
    detailed_reasoning = Column(Text, nullable=True)
    # Kyun chahiye yeh budget — CEO/CA ke liye important

    # ── Status & Timestamps ──
    status     = Column(Enum(BudgetStatus), default=BudgetStatus.DRAFT, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # onupdate=func.now() — jab bhi record update ho, timestamp automatically update ho

    # ── Relationships ──
    submitted_by_user = relationship("User", back_populates="budget_lines")
    approvals         = relationship("Approval", back_populates="budget_line")

    def __repr__(self):
        return f"<BudgetLine id={self.id} key={self.budget_key_current} status={self.status}>"

# ═══════════════════════════════════════════════════════════
# TABLE 3 — APPROVALS
# ═══════════════════════════════════════════════════════════
# Yeh table audit trail hai — kaun ne kab kya action liya
# Ek budget line pe multiple approvals ho sakte hain
# Example: Admin approve kiya, CEO reject kiya, IT Head resubmit kiya, CEO approve kiya
# Har action ek row banta hai — poora history track hota hai

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)

    budget_line_id = Column(Integer, ForeignKey("budget_lines.id"), nullable=False)
    # Kaun si budget line ke liye yeh action hai

    action_by      = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Kisne action liya — Admin ya CEO

    action         = Column(Enum(ApprovalAction), nullable=False)
    # approved / rejected / forwarded

    comment        = Column(Text, nullable=True)
    # Optional comment — rejection mein reason dena padega UI se
    # IT Head ko pata chalega kyun reject hua

    action_at      = Column(DateTime(timezone=True), server_default=func.now())

    # ── Relationships ──
    budget_line    = relationship("BudgetLine", back_populates="approvals")
    action_by_user = relationship("User", back_populates="approvals")

    def __repr__(self):
        return f"<Approval id={self.id} action={self.action} by={self.action_by}>"

# ═══════════════════════════════════════════════════════════
# TABLE 4 — DUMMY1 (Future Use)
# ═══════════════════════════════════════════════════════════
# Placeholder table — future feature ke liye
# Example use case: Budget Templates — IT Heads pre-filled templates se start kar sakein
# Ya: Notifications table — kaun kaun sa notification pending hai

class Dummy1(Base):
    __tablename__ = "dummy1"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    ref_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # ForeignKey already define kiya — jab implement karein tab easily link kar sakte
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    meta_json   = Column(Text, nullable=True)
    # meta_json — koi bhi extra data JSON string ke roop mein store karo
    # Flexible hai — future mein schema change nahi karna padega

# ═══════════════════════════════════════════════════════════
# TABLE 5 — DUMMY2 (Future Use)
# ═══════════════════════════════════════════════════════════
# Placeholder — example: Audit Logs, System Events, Email Queue

class Dummy2(Base):
    __tablename__ = "dummy2"

    id          = Column(Integer, primary_key=True, index=True)
    event_type  = Column(String(100), nullable=True)
    # "user_login", "budget_submitted", "approval_action" etc.
    event_data  = Column(Text, nullable=True)
    # JSON string — event ka poora data
    triggered_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
