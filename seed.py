# ═══════════════════════════════════════════════════════════
# seed.py — Demo Data Script
# ═══════════════════════════════════════════════════════════
# Run: python seed.py
# Yeh 5 demo users aur 6 budget entries banayega
# Prototype demonstrate karne ke liye
# ═══════════════════════════════════════════════════════════

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app import models
from app.auth import hash_password

# Tables create karo (agar already nahi hain)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

def seed():
    print("🌱 Seeding demo data...")

    # ── Clear existing data ──
    db.query(models.Approval).delete()
    db.query(models.BudgetLine).delete()
    db.query(models.Dummy2).delete()
    db.query(models.Dummy1).delete()
    db.query(models.User).delete()
    db.commit()
    print("  ✓ Cleared old data")

    # ── USERS ──────────────────────────────────────────────
    users = [
        models.User(
            full_name  = "Amit Goel",
            email      = "AmitGoel@rblbank.com",
            password   = hash_password("Pass@1234"),
            role       = models.UserRole.IT_HEAD,
            department = "Retail Banking",
            spoc_email = "Madhav.spoc@rblbank.com",
            cost_code  = "RBL-RB-CC-001",
            is_active  = True,
        ),
        models.User(
            full_name  = "Niki Kushe",
            email      = "Niki@rblbank.com",
            password   = hash_password("Pass@1234"),
            role       = models.UserRole.IT_HEAD,
            department = "Retail Banking",
            spoc_email = "Abhijit.spoc@rblbank.com",
            cost_code  = "RBL-RB-CC-001",
            is_active  = True,
        ),
        models.User(
            full_name  = "Deepa S",
            email      = "DeepaS@rblbank.com",
            password   = hash_password("Pass@1234"),
            role       = models.UserRole.IT_HEAD,
            department = "Corporate Banking",
            spoc_email = "Riya.spoc@rblbank.com",
            cost_code  = "RBL-CB-CC-002",
            is_active  = True,
        ),
        models.User(
            full_name  = "Madhav",
            email      = "Madhav@rblbank.com",
            password   = hash_password("Pass@1234"),
            role       = models.UserRole.ADMIN,
            department = "Finance",
            spoc_email = None,
            cost_code  = None,
            is_active  = True,
        ),
        models.User(
            full_name  = "Raj Shah",
            email      = "Raj@rblbank.com",
            password   = hash_password("Pass@1234"),
            role       = models.UserRole.SUPER_ADMIN,
            department = "Executive",
            spoc_email = None,
            cost_code  = None,
            is_active  = True,
        ),
    ]
    for u in users:
        db.add(u)
    db.commit()
    print("  ✓ Created 5 users (3 IT Heads, 1 Admin, 1 CEO)")

    # Refresh to get IDs
    for u in users:
        db.refresh(u)
    Amit_id   = users[0].id
    Niki_id   = users[1].id
    Deepa_id  = users[2].id
    Madhav_id = users[3].id
    Raj_id    = users[4].id

    # ── BUDGET LINES ───────────────────────────────────────
    lines_data = [
        dict(
            budget_key_current   = "RBL/IT/26/001",
            budget_key_previous  = "RBL/IT/25/001",
            old_new              = models.OldNew.OLD,
            business_name        = "Retail Banking",
            cost_code            = "RBL-RB-CC-001",
            submitted_by         = Amit_id,
            expense_sub_type     = models.ExpenseSubType.OPEX,
            description          = "Oracle DB License Annual Renewal",
            expense_description  = "Annual renewal of Oracle 19c database licenses covering production and DR environments for Retail Banking core systems.",
            application_platform = "Oracle 19c",
            vendor_name          = "Oracle India Pvt Ltd",
            resource_count       = 12,
            budget_amt_current_fy= 2400000,
            projected_consumption= 2250000,
            budget_amt_next_fy   = 2600000,
            diff_a_minus_b       = 150000,
            diff_c_minus_b       = 350000,
            diff_c_minus_a       = 200000,
            detailed_reasoning   = "Oracle licenses are mandatory for running core banking DB. 8% increase requested due to vendor price hike and additional licensing for 2 new servers.",
            status               = models.BudgetStatus.FINAL_APPROVED,
        ),
        dict(
            budget_key_current   = "RBL/IT/26/002",
            budget_key_previous  = None,
            old_new              = models.OldNew.NEW,
            business_name        = "Retail Banking",
            cost_code            = "RBL-RB-CC-001",
            submitted_by         = Amit_id,
            expense_sub_type     = models.ExpenseSubType.OPEX,
            description          = "AWS Cloud Infrastructure — Retail Apps",
            expense_description  = "Monthly AWS charges for hosting Retail Banking microservices, API gateways, and analytics workloads.",
            application_platform = "AWS",
            vendor_name          = "Amazon Web Services",
            resource_count       = None,
            budget_amt_current_fy= 4800000,
            projected_consumption= 5120000,
            budget_amt_next_fy   = 5500000,
            diff_a_minus_b       = -320000,
            diff_c_minus_b       = 380000,
            diff_c_minus_a       = 700000,
            detailed_reasoning   = "AWS usage increased due to new digital products launched in Q2. FY26-27 budget accounts for planned 15% workload growth.",
            status               = models.BudgetStatus.SUBMITTED,
        ),
        dict(
            budget_key_current   = "RBL/IT/26/003",
            budget_key_previous  = "RBL/IT/25/003",
            old_new              = models.OldNew.OLD,
            business_name        = "Retail Banking",
            cost_code            = "RBL-RB-CC-001",
            submitted_by         = Amit_id,
            expense_sub_type     = models.ExpenseSubType.CAPEX,
            description          = "Core Banking System Upgrade — Finacle 11",
            expense_description  = "One-time upgrade from Finacle 10.x to Finacle 11. Includes implementation, data migration, and UAT support.",
            application_platform = "Finacle",
            vendor_name          = "Infosys BFL",
            resource_count       = 1,
            budget_amt_current_fy= 12000000,
            projected_consumption= 9500000,
            budget_amt_next_fy   = 8000000,
            diff_a_minus_b       = 2500000,
            diff_c_minus_b       = -1500000,
            diff_c_minus_a       = -4000000,
            detailed_reasoning   = "Finacle upgrade is multi-year. Phase 1 completed in FY25-26. FY26-27 covers Phase 2 — integration with payment systems.",
            status               = models.BudgetStatus.ADMIN_APPROVED,
        ),
        dict(
            budget_key_current   = "RBL/IT/26/004",
            budget_key_previous  = None,
            old_new              = models.OldNew.NEW,
            business_name        = "Corporate Banking",
            cost_code            = "RBL-CB-CC-002",
            submitted_by         = Deepa_id,
            expense_sub_type     = models.ExpenseSubType.OPEX,
            description          = "Security Monitoring — Splunk SIEM",
            expense_description  = "Annual Splunk SIEM license for Corporate Banking threat monitoring, log management, and compliance reporting.",
            application_platform = "Splunk",
            vendor_name          = "Splunk Inc.",
            resource_count       = 5,
            budget_amt_current_fy= 1800000,
            projected_consumption= 1780000,
            budget_amt_next_fy   = 2000000,
            diff_a_minus_b       = 20000,
            diff_c_minus_b       = 220000,
            diff_c_minus_a       = 200000,
            detailed_reasoning   = "RBI mandates SIEM for all scheduled commercial banks. Splunk is our approved vendor. 11% increase for additional log sources from new applications.",
            status               = models.BudgetStatus.DRAFT,
        ),
        dict(
            budget_key_current   = "RBL/IT/26/005",
            budget_key_previous  = "RBL/IT/25/005",
            old_new              = models.OldNew.OLD,
            business_name        = "Corporate Banking",
            cost_code            = "RBL-CB-CC-002",
            submitted_by         = Deepa_id,
            expense_sub_type     = models.ExpenseSubType.OPEX,
            description          = "Microsoft 365 Enterprise Licenses",
            expense_description  = "Annual M365 E3 licenses for Corporate Banking staff. Includes Teams, SharePoint, Exchange, and Office suite.",
            application_platform = "Microsoft 365",
            vendor_name          = "Microsoft India",
            resource_count       = 200,
            budget_amt_current_fy= 3200000,
            projected_consumption= 3200000,
            budget_amt_next_fy   = 3500000,
            diff_a_minus_b       = 0,
            diff_c_minus_b       = 300000,
            diff_c_minus_a       = 300000,
            detailed_reasoning   = "Full utilization this year. 9% increase for headcount addition of 30 employees in Corporate Banking division.",
            status               = models.BudgetStatus.SUBMITTED,
        ),
        dict(
            budget_key_current   = "RBL/IT/26/006",
            budget_key_previous  = None,
            old_new              = models.OldNew.NEW,
            business_name        = "Corporate Banking",
            cost_code            = "RBL-CB-CC-002",
            submitted_by         = Deepa_id,
            expense_sub_type     = models.ExpenseSubType.CAPEX,
            description          = "Network Infrastructure Refresh — Core Switches",
            expense_description  = "Replacement of 5-year old core network switches across Corporate Banking data center. Cisco Catalyst 9K series.",
            application_platform = "Cisco Catalyst 9K",
            vendor_name          = "Cisco Systems India",
            resource_count       = 8,
            budget_amt_current_fy= 0,
            projected_consumption= 0,
            budget_amt_next_fy   = 6500000,
            diff_a_minus_b       = 0,
            diff_c_minus_b       = 6500000,
            diff_c_minus_a       = 6500000,
            detailed_reasoning   = "Current switches are EoL (End of Life) as of March 2026. No vendor support available after that. Security risk if not replaced. RFQ completed — Cisco quote obtained.",
            status               = models.BudgetStatus.DRAFT,
        ),
    ]

    for ld in lines_data:
        line = models.BudgetLine(**ld)
        db.add(line)
    db.commit()
    print(f"  ✓ Created {len(lines_data)} budget lines")

    # ── APPROVAL RECORDS ─────────────
    committed_lines = db.query(models.BudgetLine).all()

    for line in committed_lines:
        if line.status in [models.BudgetStatus.ADMIN_APPROVED, models.BudgetStatus.FINAL_APPROVED]:
            db.add(models.Approval(
                budget_line_id = line.id,
                action_by      = Madhav_id,
                action         = models.ApprovalAction.APPROVED,
                comment        = "Verified — amounts look reasonable. Forwarding to CEO.",
            ))
        if line.status == models.BudgetStatus.FINAL_APPROVED:
            db.add(models.Approval(
                budget_line_id = line.id,
                action_by      = Raj_id,
                action         = models.ApprovalAction.APPROVED,
                comment        = "Approved. Proceed.",
            ))
    db.commit()
    print("  ✓ Created approval records")

    # ── DUMMY1 (Templates placeholder) ─────────────────────
    db.add(models.Dummy1(
        title       = "OPEX Standard Template",
        description = "Pre-filled template for recurring OPEX entries",
        ref_user_id = Amit_id,
        meta_json   = '{"default_sub_type":"opex","default_resource_count":1}',
    ))
    db.add(models.Dummy1(
        title       = "CAPEX Hardware Template",
        description = "Template for hardware procurement entries",
        ref_user_id = Deepa_id,
        meta_json   = '{"default_sub_type":"capex","checklist":["RFQ done","Vendor quote","L1 approval"]}',
    ))
    db.commit()
    print("  ✓ Created Dummy1 records (templates placeholder)")

    # ── DUMMY2 (Audit log placeholder) ─────────────────────
    db.add(models.Dummy2(event_type="user_login",    event_data='{"email":"AmitGoel@rblbank.com"}', triggered_by=Amit_id))
    db.add(models.Dummy2(event_type="budget_submit", event_data='{"budget_key":"RBL/IT/26/001"}', triggered_by=Amit_id))
    db.add(models.Dummy2(event_type="approved",      event_data='{"budget_key":"RBL/IT/26/001","by":"Deepa"}', triggered_by=Deepa_id))
    db.commit()
    print("  ✓ Created Dummy2 records (audit log placeholder)")

    print("\n✅ Seed complete! Login credentials:")
    print("   IT Head   → AmitGoel@rblbank.com     / Pass@1234")
    print("   IT Head 2 → Niki@rblbank.com         / Pass@1234")
    print("   IT Head 3 → DeepaS@rblbank.com       / Pass@1234")
    print("   Admin CA  → Madhav@rblbank.com       / Pass@1234")
    print("   CEO       → Raj@rblbank.com          / Pass@1234")
    print("\n   Run server: uvicorn main:app --reload")
    print("   Open:       http://localhost:8000")

if __name__ == "__main__":
    try:
        seed()
    finally:
        db.close()