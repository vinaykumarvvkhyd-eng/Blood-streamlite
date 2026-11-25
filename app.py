import streamlit as st
import pandas as pd
import json, csv, os, re, io
from datetime import date, datetime
from collections import Counter

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_DIR, "data")
REPORT_DIR = os.path.join(APP_DIR, "reports")
JSON_FILE = os.path.join(DATA_DIR, "donors.json")
CSV_FILE = os.path.join(DATA_DIR, "donors.csv")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
STATUSES = ["Registered", "Eligible", "Donated", "Deferred"]
COLUMNS = ["donor_id", "full_name", "age", "gender", "phone", "email",
           "blood_group", "city", "camp_date", "status", "units_donated",
           "last_donation_date", "notes", "created_at"]

st.set_page_config(page_title="BloodCare | Camp Register", page_icon="🩸",
                   layout="wide", initial_sidebar_state="expanded")

# ---------- Persistence ----------
def load_records():
    try:
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                clean = []
                for item in data:
                    if isinstance(item, dict):
                        clean.append({c: item.get(c, "") for c in COLUMNS})
                return clean
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE, dtype=str).fillna("")
            return df.reindex(columns=COLUMNS, fill_value="").to_dict("records")
    except (json.JSONDecodeError, OSError, pd.errors.ParserError) as exc:
        st.warning(f"Storage file could not be read ({exc}). A fresh register is ready; the original file was not overwritten.")
    return []

def save_records(records):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    pd.DataFrame(records, columns=COLUMNS).to_csv(CSV_FILE, index=False, encoding="utf-8-sig")

if "records" not in st.session_state:
    st.session_state.records = load_records()

def as_df():
    return pd.DataFrame(st.session_state.records, columns=COLUMNS)

def validate_donor(name, age, phone, email, blood_group, camp_date, units):
    errors = []
    if not name.strip() or len(name.strip()) < 2:
        errors.append("Enter a full name containing at least 2 characters.")
    if not 18 <= int(age) <= 65:
        errors.append("Age must be between 18 and 65.")
    if not re.fullmatch(r"[6-9]\d{9}", phone.strip()):
        errors.append("Enter a valid 10-digit Indian mobile number starting with 6–9.")
    if email.strip() and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
        errors.append("Enter a valid email address or leave it blank.")
    if blood_group not in BLOOD_GROUPS:
        errors.append("Choose a valid blood group.")
    if camp_date > date.today():
        errors.append("Camp date cannot be in the future.")
    if not 0 <= int(units) <= 2:
        errors.append("Units donated must be between 0 and 2.")
    return errors

def make_id():
    existing = {str(r.get("donor_id", "")) for r in st.session_state.records}
    n = 1
    while f"BD-{n:04d}" in existing:
        n += 1
    return f"BD-{n:04d}"

def safe_text(value):
    return str(value).strip() if value is not None else ""

# ---------- Styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: radial-gradient(circle at 8% 0%, rgba(239,68,68,.12), transparent 27%), #0b1020; color: #f8fafc; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#141b31,#0e1426); border-right: 1px solid #27324b; }
.block-container { padding-top: 1.5rem; max-width: 1500px; }
.hero { padding: 26px 30px; border: 1px solid rgba(248,113,113,.25); border-radius: 22px; background: linear-gradient(120deg,rgba(127,29,29,.55),rgba(30,41,59,.92)); box-shadow: 0 18px 50px rgba(0,0,0,.25); margin-bottom: 22px; }
.hero h1 { font-family: Manrope,sans-serif; font-size: 2.15rem; margin: 0; color: white; font-weight: 800; }
.hero p { color: #fecaca; margin: 7px 0 0; }
.kpi { background: linear-gradient(145deg,#18223b,#11182b); border: 1px solid #2b3854; border-radius: 18px; padding: 18px 20px; min-height: 112px; }
.kpi .label { color:#9fb0ca; font-size:.83rem; text-transform:uppercase; letter-spacing:.08em; }
.kpi .value { color:#fff; font-size:1.9rem; font-weight:800; font-family:Manrope,sans-serif; margin-top:4px; }
.kpi .sub { color:#8fa2bf; font-size:.78rem; }
.panel { background:#121a2d; border:1px solid #26344f; border-radius:18px; padding:18px 20px; }
div[data-testid="stMetric"] { background:#17213a; border:1px solid #2b3854; padding:15px; border-radius:15px; }
.stButton>button { border-radius:10px; font-weight:700; }
div[data-testid="stForm"] { background:#121a2d; border:1px solid #26344f; border-radius:16px; padding:20px; }
.small-muted {color:#94a3b8;font-size:.85rem}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🩸 BloodCare")
    st.caption("CAMP REGISTER • COMMUNITY EDITION")
    page = st.radio("NAVIGATION", ["Overview", "Register Donor", "Donor Directory", "Analytics", "Import & Export", "About Project"])
    st.divider()
    st.markdown("**Local storage**")
    st.caption("Records are saved on this computer in JSON and CSV formats.")
    st.caption(f"Last opened: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")

df = as_df()
total = len(df)
donated = int((df["status"] == "Donated").sum()) if total else 0
eligible = int((df["status"] == "Eligible").sum()) if total else 0
units = pd.to_numeric(df["units_donated"], errors="coerce").fillna(0).sum() if total else 0
unique_groups = df["blood_group"].nunique() if total else 0

st.markdown(f"""
<div class="hero">
  <h1>🩸 Blood Donation Camp Register</h1>
  <p>A reliable, local-first system to register donors, monitor blood groups and generate camp insights.</p>
</div>
""", unsafe_allow_html=True)

if page == "Overview":
    st.subheader("Camp overview")
    c1,c2,c3,c4 = st.columns(4)
    for col, label, value, sub in [
        (c1,"Total registrations",f"{total:,}","All saved donor records"),
        (c2,"Donations completed",f"{donated:,}","Records marked as donated"),
        (c3,"Units collected",f"{int(units):,}","Total units recorded"),
        (c4,"Blood groups covered",f"{unique_groups}/8","Distinct blood groups"),
    ]:
        col.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div><div class="sub">{sub}</div></div>', unsafe_allow_html=True)
    st.write("")
    left,right = st.columns([1.15, .85])
    with left:
        st.markdown("### Blood group distribution")
        if total:
            counts = df["blood_group"].value_counts().reindex(BLOOD_GROUPS, fill_value=0)
            st.bar_chart(counts, color="#ef4444")
        else:
            st.info("No donor records yet. Add a donor to see the distribution chart.")
    with right:
        st.markdown("### Registration status")
        if total:
            status_counts = df["status"].value_counts()
            st.dataframe(status_counts.rename_axis("Status").reset_index(name="Count"), use_container_width=True, hide_index=True)
            st.progress(min(donated / total, 1.0), text=f"{donated} of {total} registrations marked donated")
        else:
            st.info("Status insights will appear here.")
    st.markdown("### Recent registrations")
    if total:
        recent = df.sort_values("created_at", ascending=False).head(5)
        st.dataframe(recent[["donor_id","full_name","blood_group","camp_date","status"]], use_container_width=True, hide_index=True)
    else:
        st.info("Your register is empty. Use **Register Donor** to add the first record.")

elif page == "Register Donor":
    st.subheader("New donor registration")
    st.caption("Fields marked * are required. Input checks run before a record is saved.")
    with st.form("donor_form", clear_on_submit=True):
        a,b,c = st.columns(3)
        name = a.text_input("Full name *", placeholder="e.g. Rahul Sharma")
        age = b.number_input("Age *", min_value=1, max_value=100, value=18, step=1)
        gender = c.selectbox("Gender", ["Prefer not to say","Female","Male","Other"])
        d,e,f = st.columns(3)
        phone = d.text_input("Mobile number *", placeholder="10-digit number")
        email = e.text_input("Email", placeholder="name@example.com")
        blood = f.selectbox("Blood group *", BLOOD_GROUPS)
        g,h,i = st.columns(3)
        city = g.text_input("City / Area", placeholder="Hyderabad")
        camp_date = h.date_input("Camp date *", value=date.today(), max_value=date.today())
        status = i.selectbox("Registration status", STATUSES, index=0)
        j,k = st.columns(2)
        units = j.number_input("Units donated", min_value=0, max_value=2, value=0, step=1)
        last_donation = k.date_input("Last donation date (optional)", value=None)
        notes = st.text_area("Notes / remarks", placeholder="Any relevant non-sensitive notes…")
        submitted = st.form_submit_button("＋ Save donor record", use_container_width=True, type="primary")
    if submitted:
        errors = validate_donor(name, age, phone, email, blood, camp_date, units)
        if status == "Donated" and units == 0:
            errors.append("For status 'Donated', enter at least 1 unit.")
        if status != "Donated" and units > 0:
            errors.append("Units can be greater than 0 only when status is 'Donated'.")
        if last_donation and last_donation > date.today():
            errors.append("Last donation date cannot be in the future.")
        if any(r.get("phone") == phone.strip() for r in st.session_state.records):
            errors.append("This mobile number is already registered.")
        if errors:
            for error in errors: st.error(error)
        else:
            record = {
                "donor_id": make_id(), "full_name": name.strip(), "age": int(age),
                "gender": gender, "phone": phone.strip(), "email": email.strip(),
                "blood_group": blood, "city": city.strip(), "camp_date": camp_date.isoformat(),
                "status": status, "units_donated": int(units),
                "last_donation_date": last_donation.isoformat() if last_donation else "",
                "notes": notes.strip(), "created_at": datetime.now().isoformat(timespec="seconds")
            }
            st.session_state.records.append(record); save_records(st.session_state.records)
            st.success(f"Donor {record['donor_id']} registered successfully. Data saved locally.")
            st.rerun()

elif page == "Donor Directory":
    st.subheader("Donor directory")
    f1,f2,f3 = st.columns([1.2,1,1])
    query = f1.text_input("Search by name, ID, phone or city")
    group_filter = f2.selectbox("Blood group", ["All"] + BLOOD_GROUPS)
    status_filter = f3.selectbox("Status", ["All"] + STATUSES)
    view = as_df()
    if query:
        mask = view.astype(str).apply(lambda col: col.str.contains(query, case=False, na=False)).any(axis=1)
        view = view[mask]
    if group_filter != "All": view = view[view["blood_group"] == group_filter]
    if status_filter != "All": view = view[view["status"] == status_filter]
    st.caption(f"Showing {len(view)} of {total} records")
    st.dataframe(view.drop(columns=["notes"], errors="ignore"), use_container_width=True, hide_index=True)
    st.divider()
    st.markdown("### Update or remove a record")
    if total:
        selected = st.selectbox("Select donor ID", df["donor_id"].tolist())
        record = next((r for r in st.session_state.records if r["donor_id"] == selected), None)
        if record:
            x,y = st.columns(2)
            new_status = x.selectbox("Change status", STATUSES, index=STATUSES.index(record["status"]) if record["status"] in STATUSES else 0, key="edit_status")
            new_notes = y.text_input("Update notes", value=record.get("notes",""), key="edit_notes")
            p,q = st.columns(2)
            if p.button("Save changes", use_container_width=True):
                record["status"] = new_status
                record["notes"] = new_notes
                if new_status != "Donated": record["units_donated"] = 0
                elif int(record.get("units_donated") or 0) == 0: record["units_donated"] = 1
                save_records(st.session_state.records); st.success("Record updated."); st.rerun()
            if q.button("Delete selected record", type="secondary", use_container_width=True):
                st.session_state.records = [r for r in st.session_state.records if r["donor_id"] != selected]
                save_records(st.session_state.records); st.success("Record deleted."); st.rerun()
    else:
        st.info("No records available to edit.")

elif page == "Analytics":
    st.subheader("Analytics & executive summary")
    if not total:
        st.info("Add or import donor records to generate analytics.")
    else:
        a,b,c,d = st.columns(4)
        a.metric("Average donor age", f"{pd.to_numeric(df['age'], errors='coerce').mean():.1f} years")
        b.metric("Donation rate", f"{donated/total*100:.1f}%")
        c.metric("Eligible registrations", eligible)
        d.metric("Average units / donor", f"{units/total:.2f}")
        left,right = st.columns(2)
        with left:
            st.markdown("#### Blood group counts")
            bg = df["blood_group"].value_counts().reindex(BLOOD_GROUPS, fill_value=0)
            st.bar_chart(bg, color="#fb7185")
        with right:
            st.markdown("#### Status breakdown")
            st.bar_chart(df["status"].value_counts(), color="#38bdf8")
        st.markdown("#### Key observations")
        most_common = df["blood_group"].mode().iloc[0] if not df["blood_group"].mode().empty else "N/A"
        least_common = df["blood_group"].value_counts().reindex(BLOOD_GROUPS, fill_value=0).idxmin()
        st.write(f"- Most represented blood group: **{most_common}**")
        st.write(f"- Least represented blood group: **{least_common}**")
        st.write(f"- Total units recorded: **{int(units)}**")
        st.write(f"- Blood groups with no registrations: **{', '.join([g for g in BLOOD_GROUPS if g not in set(df['blood_group'])]) or 'None'}**")
        if donated / total < .25:
            st.warning("Donation completion is below 25% of registrations. Review pending registrations.")
        if (df["age"].astype(float) < 18).any() or (df["age"].astype(float) > 65).any():
            st.error("Age range anomaly detected. Review imported records.")

elif page == "Import & Export":
    st.subheader("Data import & report export")
    st.markdown("#### Bulk CSV import")
    st.caption("CSV must include: full_name, age, gender, phone, email, blood_group, city, camp_date, status, units_donated.")
    uploaded = st.file_uploader("Upload donor CSV", type=["csv"])
    if uploaded:
        try:
            imp = pd.read_csv(uploaded, dtype=str).fillna("")
            required = ["full_name","age","phone","blood_group","camp_date"]
            missing = [c for c in required if c not in imp.columns]
            if missing:
                st.error("Missing required columns: " + ", ".join(missing))
            else:
                st.write(f"Preview: {len(imp)} rows")
                st.dataframe(imp.head(10), use_container_width=True, hide_index=True)
                if st.button("Validate and import rows", type="primary"):
                    added, errors = 0, []
                    for idx,row in imp.iterrows():
                        try:
                            age = int(float(row.get("age","")))
                            units = int(float(row.get("units_donated","0") or 0))
                            camp = date.fromisoformat(str(row.get("camp_date",""))[:10])
                            bg = safe_text(row.get("blood_group")).upper()
                            ph = safe_text(row.get("phone"))
                            name_i = safe_text(row.get("full_name"))
                            err = validate_donor(name_i, age, ph, safe_text(row.get("email")), bg, camp, units)
                            if err: raise ValueError("; ".join(err))
                            if any(r.get("phone") == ph for r in st.session_state.records): raise ValueError("Duplicate phone number")
                            status_i = safe_text(row.get("status")) or "Registered"
                            if status_i not in STATUSES: raise ValueError("Invalid status")
                            if (status_i == "Donated" and units < 1) or (status_i != "Donated" and units > 0): raise ValueError("Units/status mismatch")
                            rec = {c:"" for c in COLUMNS}
                            rec.update({"donor_id":make_id(),"full_name":name_i,"age":age,
                                "gender":safe_text(row.get("gender")) or "Prefer not to say","phone":ph,
                                "email":safe_text(row.get("email")),"blood_group":bg,
                                "city":safe_text(row.get("city")),"camp_date":camp.isoformat(),
                                "status":status_i,"units_donated":units,
                                "last_donation_date":safe_text(row.get("last_donation_date")),
                                "notes":safe_text(row.get("notes")),"created_at":datetime.now().isoformat(timespec="seconds")})
                            st.session_state.records.append(rec); added += 1
                        except Exception as ex:
                            errors.append(f"Row {idx+2}: {ex}")
                    save_records(st.session_state.records)
                    st.success(f"Imported {added} valid row(s).")
                    if errors: st.warning("Some rows were skipped:\n\n" + "\n".join(errors[:30]))
                    st.rerun()
        except Exception as ex:
            st.error(f"Could not process CSV: {ex}")
    st.divider()
    st.markdown("#### Export current register")
    export_df = as_df()
    csv_bytes = export_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇ Download CSV report", csv_bytes, "blood_donation_register.csv", "text/csv")
    json_bytes = json.dumps(st.session_state.records, indent=2, ensure_ascii=False).encode("utf-8")
    st.download_button("⬇ Download JSON backup", json_bytes, "blood_donors.json", "application/json")
    if total:
        md = ["# Blood Donation Camp — Executive Summary", "",
              f"- Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
              f"- Total registrations: {total}", f"- Donations completed: {donated}",
              f"- Total units: {int(units)}", "", "## Blood group counts"]
        for g in BLOOD_GROUPS: md.append(f"- {g}: {int((df['blood_group']==g).sum())}")
        md += ["", "## Status counts"]
        for s in STATUSES: md.append(f"- {s}: {int((df['status']==s).sum())}")
        st.download_button("⬇ Download Markdown summary", "\n".join(md), "executive_summary.md", "text/markdown")
        st.download_button("⬇ Download plain-text audit report", "\n".join(md), "audit_report.txt", "text/plain")
    else:
        st.info("Export buttons will include records after the first registration.")

elif page == "About Project":
    st.subheader("Project information")
    st.markdown("""
    **Project:** Blood Donation Camp Register  
    **Domain:** Safety & Community  
    **Purpose:** Manage volunteer registrations and generate blood-group counts using a beginner-friendly Python application.

    **Implemented capabilities**
    - Interactive Streamlit interface replacing the terminal menu while retaining Python business logic.
    - Defensive validation for names, age range, Indian mobile number, email, blood group, dates and donation units.
    - Local persistence in both JSON and CSV formats.
    - Search and category filters for donor records.
    - Executive summary, status indicators and blood-group visualizations.
    - CSV bulk import with row-level validation and error reporting.
    - CSV, JSON, Markdown and plain-text report downloads.

    **Technology:** Python 3.10+, Streamlit, Pandas, JSON and CSV.

    **Important:** This is a demonstration/academic register. It is not a medical eligibility assessment system. Donor eligibility must be confirmed by qualified medical personnel at the camp. Use fictional data for demos and protect real donor information.
    """)
    st.info("The PDF brief asks for local data persistence, validation, search, summaries, export options and a sample dataset. These are included in this Streamlit implementation.")

st.markdown("---")
st.markdown('<div class="small-muted">BloodCare • Blood Donation Camp Register · Local-first academic project</div>', unsafe_allow_html=True)
