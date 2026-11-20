import streamlit as st
from datetime import date, datetime
import random

st.set_page_config(
    page_title="Duggy's Whinge Machine",
    page_icon="🎻",
    layout="centered",
)

# --- CONFIG ---
DAILY_WHINGE_LIMIT = 3

ROAST_RESPONSES = [
    "🎻 World's smallest violin is warming up for you, Duggy.",
    "📋 Logged under: 'Things Nobody Can Do Anything About.'",
    "🍺 Have a sip of concrete and harden up, mate.",
    "🚨 Official Whinge Permit stamped. That's another token burned.",
    "🧱 Tell someone who cares—preferably a brick wall.",
    "🏆 Strong effort, Duggy. Olympic-level sooking right there.",
]

LOCKOUT_MESSAGES = [
    "🛑 **DAILY WHINGE QUOTA EXHAUSTED.** Come back tomorrow when you've had a Bex and a lie-down.",
    "🔒 **LOCKED OUT.** You've burned all your whinge tokens for today, Duggy. Go outside.",
    "🚫 **NO MORE SOOKING TODAY.** The Whinge Machine has overheated. Try again tomorrow.",
]

# --- PERSISTENT DAILY STATE (Survives page refreshes on the same day) ---
@st.cache_resource
def get_whinge_store():
    return {"date": str(date.today()), "entries": []}

store = get_whinge_store()
today_str = str(date.today())

# Reset automatically when a new day starts
if store["date"] != today_str:
    store["date"] = today_str
    store["entries"] = []

entries = store["entries"]
used_count = len(entries)
remaining = max(0, DAILY_WHINGE_LIMIT - used_count)

# --- UI HEADER ---
st.title("🎻 Duggy's Whinge Machine")
st.caption("One job. One quota. Zero sympathy.")

# --- QUOTA METER ---
col1, col2, col3 = st.columns(3)
col1.metric("Daily Limit", f"{DAILY_WHINGE_LIMIT}")
col2.metric("Whinges Used", f"{used_count}")
col3.metric("Remaining Today", f"{remaining}")

st.progress(min(used_count / DAILY_WHINGE_LIMIT, 1.0))

st.divider()

# --- WHINGE INPUT OR LOCKOUT ---
if remaining == 0:
    st.error(random.choice(LOCKOUT_MESSAGES))
    st.info("⏳ Your quota resets automatically at midnight.")
else:
    with st.form("duggy_whinge_form", clear_on_submit=True):
        category = st.selectbox(
            "What are we whinging about today?",
            [
                "The Refs / Umpires",
                "The Weather",
                "Work / Bosses",
                "Traffic / Drivers",
                "Bills / Prices",
                "Just Everything in General",
            ],
        )
        severity = st.select_slider(
            "Sook Severity Level",
            options=["Mild Grumble", "Proper Sook", "Full Meltdown", "Call the Ombudsman"],
            value="Proper Sook",
        )
        whinge_text = st.text_area(
            "Lodge your whinge below (make it count):",
            placeholder="Type your complaint here, Duggy...",
            max_chars=280,
        )
        submitted = st.form_submit_button("🚨 Lodge Official Whinge", use_container_width=True)

    if submitted:
        if not whinge_text.strip():
            st.warning("You can't even whinge properly—write something first!")
        else:
            roast = random.choice(ROAST_RESPONSES)
            entry = {
                "num": used_count + 1,
                "time": datetime.now().strftime("%I:%M %p"),
                "category": category,
                "severity": severity,
                "text": whinge_text.strip(),
                "roast": roast,
            }
            entries.append(entry)
            st.rerun()

# --- TODAY'S OFFICIAL WHINGE LOG ---
if entries:
    st.divider()
    st.subheader(f"📜 Today's Whinge Log ({today_str})")
    for item in reversed(entries):
        with st.container(border=True):
            st.markdown(
                f"**Whinge #{item['num']}** · `{item['time']}` · **{item['category']}** (*{item['severity']}*)"
            )
            st.write(f"> \"{item['text']}\"")
            st.caption(item["roast"])
