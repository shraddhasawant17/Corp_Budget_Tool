# ═══════════════════════════════════════════════════════════
# schemas.py — Data Validation aur Serialization (Pydantic)
# ═══════════════════════════════════════════════════════════
#
# Schema kya hota hai:
#   Ek blueprint jo batata hai ki incoming/outgoing data ka format kya hona chahiye
#
# Models vs Schemas — confusion door karo:
#   models.py  → DB tables ka structure (SQLAlchemy)
#   schemas.py → API request/response ka structure (Pydantic)
#
#   Example:
#   DB mein User ke paas: id, email, password, role, created_at
#   API response mein User: id, email, role  ← password kabhi return nahi karo!
#   Schemas yeh differentiation karte hain
#
# Pydantic kya karta hai:
#   1. Data validate karta hai — email valid hai? password length theek hai?
#   2. Type check karta hai — string aaya jahan int chahiye tha? Error dega
#   3. JSON se Python object banata hai automatically
#   4. Python object se JSON banata hai automatically
#
# Naming convention jo follow karenge:
#   UserBase       → Common fields
#   UserCreate     → Naya user banane ke liye (password include)
#   UserResponse   → API response mein kya bhejenge (password exclude)
#   UserLogin      → Login ke liye sirf email + password
# ═══════════════════════════════════════════════════════════

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime
from app.models import UserRole, BudgetStatus, ExpenseSubType, OldNew, ApprovalAction

# ═══════════════════════════════════════════════════════════
# USER SCHEMAS
# ═══════════════════════════════════════════════════════════

class UserBase(BaseModel):
    # BaseModel = Pydantic ka base class — sab schemas isse inherit karenge
    # Yahan woh fields hain jo create aur response dono mein common hain
    full_name  : str
    email      : EmailStr
    # EmailStr = special Pydantic type — automatically check karta hai valid email hai ya nahi
    # "abc" doge to error, "abc@rblbank.com" doge to accept
    role       : UserRole
    department : Optional[str] = None
    # Optional[str] = yeh field required nahi hai — None ho sakta hai
    spoc_email : Optional[EmailStr] = None
    cost_code  : Optional[str] = None

class UserCreate(UserBase):
    # UserBase ke saare fields + password
    # Kyun alag class: password sirf create karte waqt chahiye
    # Response mein password kabhi nahi denge
    password   : str = Field(..., min_length=8)
    # Field(...) = required field
    # min_length=8 = kam se kam 8 characters zaroori
    # "abc" doge to Pydantic automatically 422 error dega

class UserResponse(UserBase):
    # Yeh API response mein jayega — password nahi
    id         : int
    is_active  : bool
    created_at : datetime

    class Config:
        # orm_mode = True batata hai Pydantic ko ki yeh SQLAlchemy object hai
        # Matlab User(...) object directly pass kar sakte hain — dict banana nahi padega
        from_attributes = True

class UserLogin(BaseModel):
    # Sirf login ke liye — email + password
    email    : EmailStr
    password : str

class TokenResponse(BaseModel):
    # Login successful hone ke baad yeh return hoga
    rbl_token : str
    # JWT token — browser isko store karega aur har request ke saath bhejega
    token_type   : str = "bearer"
    # "bearer" = standard HTTP auth type
    role         : UserRole
    full_name    : str
    user_id      : int

# ═══════════════════════════════════════════════════════════
# BUDGET LINE SCHEMAS
# ═══════════════════════════════════════════════════════════

class BudgetLineBase(BaseModel):
    # Common fields — create aur update dono mein
    old_new               : OldNew
    budget_key_previous   : Optional[str] = None
    business_name         : str
    expense_sub_type      : ExpenseSubType
    description           : str = Field(..., max_length=200)
    expense_description   : Optional[str] = None
    application_platform  : Optional[str] = None
    vendor_name           : Optional[str] = None
    resource_count        : Optional[int] = Field(None, ge=0)
    # ge=0 = greater than or equal to 0 — negative count allowed nahi
    budget_amt_current_fy : float = Field(..., gt=0)
    # gt=0 = greater than 0 — zero ya negative budget allowed nahi
    projected_consumption : float = Field(..., ge=0)
    budget_amt_next_fy    : float = Field(..., gt=0)
    detailed_reasoning    : Optional[str] = None

    @validator('budget_key_previous', always=True)
    def validate_prev_key(cls, v, values):
        # Custom validator — OLD entries ke liye previous key required hai
        # 'values' mein already validated fields hain
        if values.get('old_new') == OldNew.OLD and not v:
            raise ValueError("Old entries ke liye Previous Year Budget Key required hai")
        return v

class BudgetLineCreate(BudgetLineBase):
    # Naya budget line create karne ke liye
    # budget_key_current system generate karega — user nahi dega
    # submitted_by bhi JWT token se milega — user nahi dega
    # Isliye yahan koi extra field nahi
    pass

class BudgetLineUpdate(BaseModel):
    # Partial update — sirf jo fields aaye woh update karo (PATCH behavior)
    # Sab Optional hain — matlab koi bhi ek field update kar sakte hain
    description           : Optional[str] = None
    expense_description   : Optional[str] = None
    application_platform  : Optional[str] = None
    vendor_name           : Optional[str] = None
    resource_count        : Optional[int] = None
    budget_amt_current_fy : Optional[float] = None
    projected_consumption : Optional[float] = None
    budget_amt_next_fy    : Optional[float] = None
    detailed_reasoning    : Optional[str] = None

class BudgetLineResponse(BudgetLineBase):
    # API response mein poori detail
    id                    : int
    budget_key_current    : str
    cost_code             : str
    status                : BudgetStatus
    diff_a_minus_b        : Optional[float] = None
    diff_c_minus_b        : Optional[float] = None
    diff_c_minus_a        : Optional[float] = None
    submitted_by          : int
    created_at            : datetime
    updated_at            : Optional[datetime] = None

    class Config:
        from_attributes = True

class BudgetLineSummary(BaseModel):
    # Dashboard cards ke liye — sirf summary, full detail nahi
    id                    : int
    budget_key_current    : str
    business_name         : str
    description           : str
    expense_sub_type      : ExpenseSubType
    application_platform  : Optional[str] = None
    budget_amt_current_fy : float
    projected_consumption : float
    budget_amt_next_fy    : float
    diff_a_minus_b        : Optional[float] = None
    status                : BudgetStatus
    submitted_by          : int

    class Config:
        from_attributes = True

# ═══════════════════════════════════════════════════════════
# APPROVAL SCHEMAS
# ═══════════════════════════════════════════════════════════

class ApprovalCreate(BaseModel):
    # Admin ya CEO jab approve/reject kare tab yeh data aayega
    budget_line_id : int
    action         : ApprovalAction
    comment        : Optional[str] = None

    @validator('comment')
    def comment_required_on_rejection(cls, v, values):
        # Reject karte waqt comment required hai
        # IT Head ko pata chahiye kyun reject hua
        if values.get('action') == ApprovalAction.REJECTED and not v:
            raise ValueError("Rejection ke saath comment/reason dena zaroori hai")
        return v

class ApprovalResponse(BaseModel):
    id             : int
    budget_line_id : int
    action_by      : int
    action         : ApprovalAction
    comment        : Optional[str] = None
    action_at      : datetime

    class Config:
       from_attributes = True

# ═══════════════════════════════════════════════════════════
# DASHBOARD SCHEMAS
# ═══════════════════════════════════════════════════════════

class DashboardKPI(BaseModel):
    # Dashboard ke top cards ke liye
    total_budget      : float  # SUM of all budget_amt_current_fy
    total_opex        : float  # SUM where expense_sub_type = OPEX
    total_capex       : float  # SUM where expense_sub_type = CAPEX
    total_budget_keys : int    # COUNT DISTINCT budget keys
    total_it_heads    : int    # COUNT DISTINCT IT heads

class ITHeadBudgetData(BaseModel):
    # Bar chart ke liye — IT Head wise budget
    it_head_name    : str
    total_budget    : float
    total_projected : float

class DashboardResponse(BaseModel):
    kpi           : DashboardKPI
    it_head_data  : List[ITHeadBudgetData]
    # List[ITHeadBudgetData] = multiple IT heads ka data

# ═══════════════════════════════════════════════════════════
# DUMMY SCHEMAS (Future Use)
# ═══════════════════════════════════════════════════════════

class Dummy1Base(BaseModel):
    title       : Optional[str] = None
    description : Optional[str] = None
    ref_user_id : Optional[int] = None
    meta_json   : Optional[str] = None

class Dummy1Create(Dummy1Base):
    pass

class Dummy1Response(Dummy1Base):
    id         : int
    is_active  : bool
    created_at : datetime
    class Config:
        from_attributes = True

class Dummy2Base(BaseModel):
    event_type   : Optional[str] = None
    event_data   : Optional[str] = None
    triggered_by : Optional[int] = None

class Dummy2Create(Dummy2Base):
    pass

class Dummy2Response(Dummy2Base):
    id         : int
    created_at : datetime
    class Config:
        from_attributes = True
