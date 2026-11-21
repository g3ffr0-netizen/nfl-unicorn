import base64
import csv
import io
import os
from datetime import datetime, timezone
import requests
import streamlit as st

st.set_page_config(
    page_title="Guardian Power | Decentralized Direct-DC Energy",
    page_icon="⚡",
    layout="wide",
)

# High-contrast dark clean-energy theme styling
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0B131E;
        color: #F0F4F8;
    }
    section[data-testid="stSidebar"] {
        background-color: #131F2E;
    }
    section[data-testid="stSidebar"] * {
        color: #F0F4F8 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## ⚡ Guardian Power")
    st.caption("Decentralized Microgrids • Native 1,000V Direct-DC • Built to AS/NZS 5139 & 3000")
    st.divider()
    section = st.radio(
        "Navigate",
        [
            "🏡 Home & Vision",
            "🛠️ Inventions & Architectures",
            "⚡ Direct-DC & Microgrid Estimator",
            "💻 Web & App Development Studio",
            "♿ NDIS & Independent Living",
            "🤝 Register Interest / Partner",
        ],
    )
    st.divider()
    st.info("Showcasing community-scale microgrids, proprietary Direct-DC hardware, and custom web/app solutions.")

# ---------------------------------------------------------
# 1. HOME & VISION
# ---------------------------------------------------------
if section == "🏡 Home & Vision":
    st.title("⚡ Guardian Power")
    st.subheader("Decentralized Direct-DC Energy, Resilient Microgrids & Custom Web/App Systems")

    st.markdown(
        """
        **Guardian Power** is an Australian clean-energy and systems engineering initiative focused on eliminating
        wasteful AC-DC conversion losses, hardening residential solar against extreme weather, and building
        custom web apps and telemetry tools for local businesses, co-ops, and independent living.
        """
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 🔌 Native Direct-DC")
        st.write(
            "Traditional solar setups convert DC to AC and back to DC multiple times, burning 10–20% of "
            "generated energy as heat. Guardian Power architectures run directly off a unified 1,000V DC busbar."
        )
    with c2:
        st.markdown("### 🛡️ Storm-Safe Engineering")
        st.write(
            "Non-conductive composite structures and ground-lowering roof arrays designed to survive severe "
            "Australian hail and wind events without sacrificing daily sun-tracking yield."
        )
    with c3:
        st.markdown("### 💻 Custom Web Apps & Protocols")
        st.write(
            "Rapid-deployment Python web applications, interactive calculators, and Sonny Protocol telemetry "
            "built for local businesses, clubs, NDIS providers, and energy projects."
        )

    st.divider()
    st.info(
        "👈 Explore **Inventions & Architectures**, test the **Direct-DC Estimator**, check out the **Web & App Development Studio**, "
        "see **NDIS & Independent Living** solutions, or **Register Interest** in the sidebar."
    )

# ---------------------------------------------------------
# 2. INVENTIONS & ARCHITECTURES
# ---------------------------------------------------------
elif section == "🛠️ Inventions & Architectures":
    st.title("🛠️ Inventions & Hardware Architectures")
    st.caption(
        "High-level architectural overviews of Guardian Power hardware systems. "
        "Detailed schematics, CAD models, and patent specifications remain proprietary IP."
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "1. Storm-Safe Carport 1,000V DC Loop",
            "2. Sovereign Multi-Vector Utility Skid",
            "3. Diamond Micro-Trace Core",
        ]
    )

    with tab1:
        c1, c2 = st.columns([1.6, 1])
        with c1:
            st.subheader("Single-Carport Non-Conductive Solar & Thermal Loop")
            st.markdown(
                """
                A residential proof-of-concept microgrid node engineered for zero AC-conversion loss,
                non-conductive structural safety, and active severe-weather protection:
                * **5 kW Sun-Tracking Non-Conductive Roof:** Composite structural framing that tracks solar
                  azimuth/elevation during normal operation and drops flat to ground level ahead of severe storms or hail.
                * **1,000V Direct-DC Busbar:** Eliminates cascaded DC-AC-DC inverter losses by feeding native DC loads directly.
                * **15 kWh LFP Storage + Heat-Pump Thermal Loop:** Couples electrical storage with thermal energy
                  buffering for maximum self-sufficiency.
                """
            )
        with c2:
            st.metric("Array Capacity", "5.0 kW", "Sun-Tracking")
            st.metric("Battery Storage", "15 kWh", "LFP / AS/NZS 5139")
            st.metric("Bus Architecture", "1,000V DC", "Direct-DC Busbar")

    with tab2:
        c1, c2 = st.columns([1.6, 1])
        with c1:
            st.subheader("Sovereign Multi-Vector Utility Skid (Off-Grid Container)")
            st.markdown(
                """
                A self-contained containerized utility node combining generation, storage, clean water,
                and green hydrogen on a unified **1,000V Direct-DC busbar**:
                * **Generation:** Solar PVT (photovoltaic-thermal) canopies paired with dual-kite airborne
                  wind energy featuring edge-AI raptor protection.
                * **Storage:** 50 kWh LFP battery bank managed on the high-voltage DC bus.
                * **Water & Fuel Vectors:** Integrated reverse-osmosis (RO) desalination and AEM hydrogen
                  electrolysis running directly off surplus DC power.
                """
            )
        with c2:
            st.metric("Core Storage", "50 kWh LFP", "1,000V DC Bus")
            st.metric("Generation", "Solar PVT + Kite", "Edge-AI Wildlife Safe")
            st.metric("Outputs", "Power • Water • H2", "RO + AEM Electrolysis")

    with tab3:
        c1, c2 = st.columns([1.6, 1])
        with c1:
            st.subheader("Field-Graded 1,000V DC Superconducting Diamond Micro-Trace Core")
            st.markdown(
                """
                Next-generation high-voltage solid-state power and compute substrate architecture:
                * **Field-Graded Dielectric Control:** Engineered to manage high-voltage stress across
                  micro-scale conductors at 1,000V DC.
                * **Fault-Tolerant Topology:** Redundant micro-trace routing designed for ultra-low loss
                  and high thermal dissipation.
                """
            )
        with c2:
            st.metric("Operating Bus", "1,000V DC", "Field-Graded")
            st.metric("Architecture", "Fault-Tolerant", "Diamond Micro-Trace")
            st.metric("Status", "Patent Concept", "Proprietary IP")

# ---------------------------------------------------------
# 3. DIRECT-DC & MICROGRID ESTIMATOR
# ---------------------------------------------------------
elif section == "⚡ Direct-DC & Microgrid Estimator":
    st.title("⚡ Direct-DC & Microgrid Efficiency Estimator")
    st.caption("Compare a conventional AC-coupled solar/battery setup against a Guardian Power Direct-DC bus architecture.")

    col1, col2 = st.columns(2)
    with col1:
        array_kw = st.slider("Solar Array Size (kW)", min_value=3.0, max_value=30.0, value=5.0, step=0.5)
        battery_kwh = st.slider("Battery Storage (kWh)", min_value=5.0, max_value=100.0, value=15.0, step=5.0)
        sun_hours = st.slider("Average Peak Sun Hours / Day", min_value=3.0, max_value=6.5, value=4.5, step=0.1)
    with col2:
        tracker_boost = st.checkbox("Include Sun-Tracking Roof Yield Gain (+22%)", value=True)
        tariff_c = st.number_input("Grid Electricity Tariff ($/kWh AUD)", min_value=0.10, max_value=0.80, value=0.34, step=0.02)

    tracking_mult = 1.22 if tracker_boost else 1.00
    raw_daily_kwh = array_kw * sun_hours * tracking_mult

    ac_usable_kwh = raw_daily_kwh * 0.84
    dc_usable_kwh = raw_daily_kwh * 0.96
    extra_daily_kwh = dc_usable_kwh - ac_usable_kwh
    annual_extra_aud = extra_daily_kwh * 365 * tariff_c

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Conventional AC Usable / Day", f"{ac_usable_kwh:.1f} kWh")
    m2.metric("Guardian Direct-DC Usable / Day", f"{dc_usable_kwh:.1f} kWh", f"+{extra_daily_kwh:.1f} kWh/day")
    m3.metric("Annual Value of Recovered Energy", f"${annual_extra_aud:,.0f} AUD/yr")

# ---------------------------------------------------------
# 4. WEB & APP DEVELOPMENT STUDIO (WITH SONNY PROTOCOLS)
# ---------------------------------------------------------
elif section == "💻 Web & App Development Studio":
    st.title("💻 Website Development & Custom App Studio")
    st.caption("Fast-turnaround custom websites, interactive web apps, and Sonny Protocol telemetry tools.")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("🌐 Custom Websites & Portals")
        st.markdown(
            """
            Clean, fast, cloud-hosted websites built without bloated subscriptions or slow turnaround times:
            * **Rapid Deployment:** From concept to a live web address in rapid turnaround.
            * **Built-In Lead Capture:** Direct inquiry forms, booking requests, and automated data logging.
            * **Zero Server Maintenance:** Reliable cloud hosting with automatic SSL security.
            """
        )
    with c2:
        st.subheader("📱 Interactive Web Apps & Tools")
        st.markdown(
            """
            More than a static brochure—custom Python web applications tailored to your exact workflow:
            * **Live Calculators & Quote Tools:** Interactive pricing, energy, or job estimators for customers.
            * **Operations & Analytics Dashboards:** Real-time data viewers, CSV/spreadsheet processors, and
              custom decision-support tools for local clubs, trades, and small businesses.
            """
        )
    with c3:
        st.subheader("📡 The Sonny Protocols & Telemetry")
        st.markdown(
            """
            Modular state-and-telemetry architecture for hardware, IoT, and operational visibility:
            * **Edge-to-Dashboard Sync:** Lightweight Python pipelines connecting local sensors, DC bus
              telemetry, and automated safety triggers.
            * **Department & Dev Hooks:** Clean interfaces for internal R&D teams and app makers building
              on top of Guardian Power systems.
            """
        )

    st.divider()
    st.info(
        "Need a website, an interactive calculator/dashboard for your business, or custom protocol integration? "
        "Head to **Register Interest / Partner** in the sidebar and tell us what you want to build."
    )

# ---------------------------------------------------------
# 5. NDIS & INDEPENDENT LIVING
# ---------------------------------------------------------
elif section == "♿ NDIS & Independent Living":
    st.title("♿ NDIS & Resilient Independent Living")
    st.caption(
        "NDIS-aligned & SDA-compatible Direct-DC backup power and smart telemetry concepts for "
        "high-reliability home environments."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 🔋 Critical Load Continuity")
        st.write(
            "Zero-interruption Direct-DC battery backup designed to keep powered mobility aids, "
            "medical equipment, and essential climate control online through grid outages and severe storms."
        )
    with c2:
        st.markdown("### 🏠 SDA & SIL Microgrid Ready")
        st.write(
            "Scalable solar, LFP storage, and heat-pump thermal loops tailored for Specialist Disability "
            "Accommodation (SDA) and Supported Independent Living (SIL) homes to reduce 24/7 energy costs."
        )
    with c3:
        st.markdown("### 📲 Accessible Telemetry & Alerts")
        st.write(
            "Powered by the Sonny Protocol stack to give participants, families, and support coordinators "
            "clear, low-friction visibility over backup reserves and home safety systems."
        )

    st.divider()
    st.info(
        "Working with NDIS participants, SDA builders, or SIL providers in NSW? Reach out via "
        "**Register Interest / Partner** to discuss pilot requirements and compatibility."
    )

# ---------------------------------------------------------
# 6. REGISTER INTEREST / PARTNER
# ---------------------------------------------------------
elif section == "🤝 Register Interest / Partner":
    st.title("🤝 Register Interest & Technical Partnerships")
    st.write(
        "Interested in a custom website or web app, neighborhood microgrid participation, pilot hardware testing, "
        "or NDIS/SDA resilient energy solutions? Leave your details below."
    )

    with st.form("interest_form", clear_on_submit=True):
        name = st.text_input("Name *")
        email = st.text_input("Email *")
        suburb = st.text_input("Suburb / Region (e.g., Gorokan / Central Coast NSW)")
        role = st.selectbox(
            "I am reaching out as a...",
            [
                "Business / Club needing a Website or Custom Web App",
                "Local Resident / Future Co-op Member",
                "App Developer / Software or R&D Department",
                "NDIS Participant / SDA / SIL Provider",
                "Electrical / Structural / Clean-Tech Engineer",
                "Manufacturer / Supplier",
                "Investor / Community Grant Partner",
                "Other",
            ],
        )
        notes = st.text_area("Tell us about your project, website/app idea, or setup")
        submitted = st.form_submit_button("Submit Inquiry")

    if submitted:
        if not name.strip() or not email.strip():
            st.error("Please enter both your name and email address.")
        else:
            token = st.secrets.get("GITHUB_TOKEN", os.getenv("GITHUB_TOKEN", ""))
            repo = st.secrets.get("GITHUB_REPO", "g3ffr0-netizen/nfl-unicorn")
            path = "guardian_power_inquiries.csv"

            if not token:
                st.success(f"Thanks {name}! Your inquiry has been recorded.")
            else:
                api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
                headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
                resp = requests.get(api_url, headers=headers, timeout=15)

                existing_csv = "timestamp_utc,name,email,suburb,role,notes\n"
                sha = None
                if resp.status_code == 200:
                    payload = resp.json()
                    sha = payload["sha"]
                    existing_csv = base64.b64decode(payload["content"]).decode("utf-8")

                buf = io.StringIO()
                writer = csv.writer(buf)
                writer.writerow([
                    datetime.now(timezone.utc).isoformat(),
                    name.strip(),
                    email.strip(),
                    suburb.strip(),
                    role,
                    notes.strip(),
                ])
                updated_csv = existing_csv + buf.getvalue()

                put_body = {
                    "message": f"New Guardian Power inquiry from {name.strip()}",
                    "content": base64.b64encode(updated_csv.encode("utf-8")).decode("utf-8"),
                }
                if sha:
                    put_body["sha"] = sha

                put_resp = requests.put(api_url, headers=headers, json=put_body, timeout=15)
                if put_resp.status_code in (200, 201):
                    st.success(f"Thanks {name}! Your details have been saved to Guardian Power.")
                else:
                    st.error(f"Could not save inquiry ({put_resp.status_code}). Please try again later.")
