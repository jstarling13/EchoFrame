import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

st.set_page_config(page_title="Apollo Prospect Puller", page_icon="🎯", layout="wide")

st.title("🎯 Apollo Prospect Puller")
st.caption("Pull verified business owner contacts from Apollo.io — name, email, phone, company, industry")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Apollo API Key", type="password", placeholder="your apollo api key")
    st.divider()

    st.subheader("Location")
    city  = st.text_input("City",  value="Columbus")
    state = st.text_input("State", value="Georgia")

    st.subheader("Target Industries")
    industry_map = {
        "Home Services (HVAC, Plumbing, Electrical)": "home services",
        "Construction & Contractors":                  "construction",
        "Salons, Barbershops & Beauty":                "health wellness fitness",
        "Restaurants & Food":                          "food beverages",
        "Gyms & Fitness Studios":                      "health wellness fitness",
        "Accounting & Bookkeeping":                    "accounting",
        "Law Firms":                                   "legal services",
        "Marketing Agencies":                          "marketing advertising",
        "Auto Repair":                                 "automotive",
        "Landscaping":                                 "landscaping",
        "Real Estate":                                 "real estate",
        "Dental / Medical Offices":                    "medical practice",
    }
    selected_industries = st.multiselect(
        "Select industries",
        list(industry_map.keys()),
        default=["Home Services (HVAC, Plumbing, Electrical)"]
    )
    custom_industry = st.text_input("Or type a custom keyword", placeholder="e.g. roofing")

    st.subheader("Company Size")
    size_options = {
        "1-10 employees (solo / tiny)":   "1,10",
        "1-20 employees (small)":         "1,20",
        "1-50 employees (small-medium)":  "1,50",
        "10-50 employees":                "10,50",
    }
    size_label = st.selectbox("Employee range", list(size_options.keys()), index=2)
    emp_range  = size_options[size_label]

    st.subheader("Decision Maker Titles")
    titles = st.multiselect(
        "Include titles",
        ["owner", "founder", "CEO", "president", "co-owner", "managing partner", "principal"],
        default=["owner", "founder", "CEO", "president"]
    )

    st.subheader("Volume")
    max_results = st.slider("Max contacts to pull", 10, 500, 100, step=10)

    st.divider()
    st.caption("Apollo deducts credits for email reveals. Check your plan limits before pulling large lists.")

# ── Apollo API helpers ────────────────────────────────────────────────────────
BASE_URL = "https://api.apollo.io/v1"

def search_people(api_key, titles, location_str, industry_keywords, emp_range, page=1, per_page=100):
    headers = {
        "Content-Type":  "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key":     api_key,
    }

    # Build keyword string from selected industries
    kw_parts = []
    if industry_keywords:
        kw_parts.extend(industry_keywords)

    payload = {
        "person_titles":                      titles,
        "person_locations":                   [f"{location_str}"],
        "organization_num_employees_ranges":  [emp_range],
        "per_page":                           min(per_page, 100),
        "page":                               page,
    }

    if kw_parts:
        payload["q_organization_keyword_tags"] = kw_parts

    r = requests.post(
        f"{BASE_URL}/mixed_people/search",
        headers=headers,
        json=payload,
        timeout=15,
    )

    if r.status_code == 401:
        st.error("Invalid API key — check your Apollo key and try again.")
        return None, 0
    if r.status_code == 429:
        st.warning("Rate limited — waiting 5 seconds...")
        time.sleep(5)
        return search_people(api_key, titles, location_str, industry_keywords, emp_range, page, per_page)
    if not r.ok:
        st.error(f"Apollo API error {r.status_code}: {r.text[:300]}")
        return None, 0

    data = r.json()
    people     = data.get("people", [])
    total      = data.get("pagination", {}).get("total_entries", 0)
    return people, total


def parse_person(p):
    org = p.get("organization") or {}
    return {
        "name":              p.get("name", ""),
        "title":             p.get("title", ""),
        "email":             p.get("email", ""),
        "email_status":      p.get("email_status", ""),
        "phone":             (p.get("phone_numbers") or [{}])[0].get("sanitized_number", ""),
        "linkedin":          p.get("linkedin_url", ""),
        "company":           org.get("name", ""),
        "industry":          org.get("industry", ""),
        "employees":         org.get("num_employees", ""),
        "company_city":      org.get("city", ""),
        "company_state":     org.get("state", ""),
        "company_website":   org.get("website_url", ""),
        "company_phone":     org.get("phone", ""),
    }


# ── Main ──────────────────────────────────────────────────────────────────────
location_str = f"{city}, {state}, United States"

# Build industry keyword list
industry_keywords = []
for label in selected_industries:
    kw = industry_map.get(label, "")
    if kw and kw not in industry_keywords:
        industry_keywords.append(kw)
if custom_industry:
    industry_keywords.append(custom_industry.lower())

# Preview
st.info(
    f"**Target:** {', '.join(titles)} | "
    f"**Location:** {city}, {state} | "
    f"**Industries:** {', '.join(selected_industries[:2]) or custom_industry or 'All'} | "
    f"**Company size:** {size_label} | "
    f"**Max:** {max_results} contacts"
)

col1, col2 = st.columns([1, 3])
with col1:
    run = st.button("🚀 Pull Prospects", type="primary", use_container_width=True, disabled=not api_key)
with col2:
    if not api_key:
        st.warning("Add your Apollo API key in the sidebar to get started.")

if run and api_key:
    st.divider()
    progress    = st.progress(0)
    status_text = st.empty()

    all_people = []
    page       = 1
    per_page   = min(100, max_results)
    total      = None

    while len(all_people) < max_results:
        remaining = max_results - len(all_people)
        fetch     = min(per_page, remaining)

        status_text.text(f"Pulling page {page}... ({len(all_people)} contacts so far)")
        people, total = search_people(
            api_key, titles, location_str,
            industry_keywords, emp_range,
            page=page, per_page=fetch
        )

        if people is None:
            break
        if not people:
            status_text.text(f"No more results. Total found: {len(all_people)}")
            break

        all_people.extend(people)

        if total is not None:
            progress.progress(min(len(all_people) / min(max_results, total + 1), 1.0))

        if len(people) < fetch:
            break

        page += 1
        time.sleep(0.3)

    progress.progress(1.0)
    status_text.text(f"Done — {len(all_people)} contacts pulled.")

    if all_people:
        df = pd.DataFrame([parse_person(p) for p in all_people])

        # ── Metrics ──
        st.subheader(f"Results: {len(df)} contacts")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total contacts",   len(df))
        m2.metric("With email",       df["email"].ne("").sum())
        m3.metric("With phone",       df["phone"].ne("").sum())
        m4.metric("Verified emails",  (df["email_status"] == "verified").sum())

        # ── Filters ──
        st.subheader("Filter results")
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            email_only  = st.checkbox("Has email", value=True)
        with fc2:
            phone_only  = st.checkbox("Has phone", value=False)
        with fc3:
            verified_only = st.checkbox("Verified email only", value=False)

        filtered = df.copy()
        if email_only:    filtered = filtered[filtered["email"].ne("")]
        if phone_only:    filtered = filtered[filtered["phone"].ne("")]
        if verified_only: filtered = filtered[filtered["email_status"] == "verified"]

        # Priority score: has email + has phone + verified = best targets
        filtered["priority"] = (
            filtered["email"].ne("").astype(int) +
            filtered["phone"].ne("").astype(int) +
            (filtered["email_status"] == "verified").astype(int)
        )
        filtered = filtered.sort_values("priority", ascending=False)

        st.caption(f"Showing {len(filtered)} of {len(df)} contacts after filters")

        display_cols = ["name", "title", "company", "industry", "email", "phone", "company_city", "employees", "linkedin"]
        st.dataframe(filtered[display_cols], use_container_width=True, height=420)

        # ── Top targets callout ──
        top = filtered[(filtered["email"].ne("")) & (filtered["phone"].ne("")) & (filtered["email_status"] == "verified")]
        if not top.empty:
            st.success(f"🎯 **{len(top)} priority targets** — verified email + phone number (highest quality outreach)")

        # ── Export ──
        st.divider()
        ts  = datetime.now().strftime("%Y%m%d_%H%M")
        csv = filtered.to_csv(index=False)
        st.download_button(
            label="⬇️ Download prospect list CSV",
            data=csv,
            file_name=f"prospects_{city}_{ts}.csv",
            mime="text/csv",
            type="primary"
        )

        # ── Outreach message generator ──
        st.divider()
        st.subheader("📧 Quick outreach message")
        sample_name    = filtered["name"].iloc[0]    if len(filtered) > 0 else "Sarah"
        sample_company = filtered["company"].iloc[0] if len(filtered) > 0 else "their business"
        sample_industry = filtered["industry"].iloc[0] if len(filtered) > 0 else "home services"

        st.code(f"""Subject: Free business clarity report for {sample_company}

Hi {sample_name.split()[0]},

I produce monthly financial clarity reports for {sample_industry} businesses in {city} — plain-English breakdowns of where money is going, what's leaking, and exactly what to do about it.

I put together a free sample for a business like {sample_company}. It takes 15 minutes to walk through and most owners find at least one thing worth acting on immediately.

Worth a quick call this week?

[Your name]
[Your phone]""", language="text")

        st.caption("Customize the industry reference per contact for higher reply rates.")

    else:
        st.warning("No results returned. Try loosening your filters — broader industry, larger radius, or more titles.")

elif run and not api_key:
    st.error("Add your Apollo API key in the sidebar first.")

with st.expander("How to find your Apollo API key"):
    st.markdown("""
1. Log into [app.apollo.io](https://app.apollo.io)
2. Go to **Settings → Integrations → API**
3. Copy your API key
4. Paste it in the sidebar

**Credit usage:** Searching costs minimal credits. Email reveals cost 1 credit each on most plans. 
If you're on a free or basic plan, focus on contacts where Apollo already shows the email without revealing.
    """)
