import streamlit as st
import json
from openai import OpenAI

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 0.  Initialise session‑state hooks
# ────────────────────────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    # {persona_name|"ALL": [(question, answer), …]}
    st.session_state.chat_history: dict[str, list[tuple[str, str]]] = {}
if "question_input" not in st.session_state:
    st.session_state.question_input = ""

# ────────────────────────────────────────────────────────────────────────────────
# 1.  Load persona data and OpenAI client
# ────────────────────────────────────────────────────────────────────────────────
with open("personas.json", "r", encoding="utf-8") as f:
    persona_data: list[dict] = json.load(f)["personas"]

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Segment summaries (unchanged)
segment_summaries = {
    "Next Generation Investors (18–24 years)": "These young investors are tech‑savvy, socially conscious, and ambitious. They seek financial independence, value creativity and personal freedom, and are primarily influenced by peers and social media trends. Their risk tolerance is generally high, and they prefer platforms that are interactive and visually engaging.",
    "Emerging Wealth Builders (25–34 years)": "These individuals are in the early stages of wealth accumulation, often with moderate to high investing experience. They are ambitious and analytical, driven by goals like starting a business, financial freedom, and buying a home. They value innovation, entrepreneurship, and sustainability, and tend to be comfortable with moderate to high risk in pursuit of growth.",
    "Established Accumulators (35–49 years)": "Often juggling career and family, these investors focus on financial security and long‑term planning. They are pragmatic and goal‑oriented, aiming to fund children’s education, grow wealth, and prepare for retirement. They seek expert advice and tend to have a moderate risk tolerance, balancing growth with asset protection.",
    "Pre‑Retirees (50–64 years)": "Pre‑retirees are focused on preserving wealth, planning for a secure retirement, and leaving a legacy. They are typically analytical, cautious, and value expert guidance. Stability and income generation are top priorities, and they often consult multiple professionals before making decisions. Risk tolerance is generally low to moderate.",
    "Retirees (65+ years)": "This segment prioritises stability, simplicity, and preserving capital. Most are retired professionals who rely on trusted advisors and conservative investments to support their lifestyle and family. Their values include family, integrity, and community, and they prefer face‑to‑face services and clear, jargon‑free information. Their risk tolerance is low."
}

# ────────────────────────────────────────────────────────────────────────────────
# 2.  Streamlit page setup & basic styles
# ────────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Burgo's Persona Portal", layout="centered", page_icon="💬")

st.markdown(
    """
    <style>
        /* Slim border & radius on all Streamlit buttons */
        .stButton>button {border:1px solid #485cc7; border-radius:8px}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🧠 Matt's Test Persona Portal")

# About‑tool callout  ───────────────────────────────────────────────────────────

st.markdown(
    """
    <div style="background-color:#f0f2f6; padding:20px; border-left:6px solid #485cc7; border-radius:10px; margin-bottom:25px">
        <h4 style="margin-top:0;">ℹ️ About This Tool</h4>
        <p>This tool uses AI‑generated investor personas — built from real Australian investor research — to simulate how different segments might respond to your ideas.</p>
        <p>Each persona is built on rich attributes — including goals, values, behaviours, concerns, and communication preferences — informed by studies such as the ASX Investor Study, Investment Trends reports, and Stake member surveys.</p>
        <p>GPT‑4o emulates how these personas might realistically think, feel, and respond, based on their individual attributes.</p>
        <p>The goal? Give marketing and product teams a quick, easy way to test ideas and spark fresh thinking — without commissioning full‑scale research.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Intro blurb
st.markdown(
    "Welcome to the Persona Portal! Select a persona to view their profile and ask questions to gain insights into different investor perspectives.")

# ────────────────────────────────────────────────────────────────────────────────
# 3.  Segment filter & overview accordion
# ────────────────────────────────────────────────────────────────────────────────
segments = sorted({p["segment"] for p in persona_data})
selected_segment = st.selectbox("Filter by Segment", ["All"] + segments)

if selected_segment == "All":
    with st.expander("🔍 Segment cheat‑sheet"):
        for seg, blurb in segment_summaries.items():
            st.markdown(f"**{seg}**  \n{blurb}\n")
elif selected_segment in segment_summaries:
    with st.expander("🔍 Segment overview", expanded=True):
        st.write(segment_summaries[selected_segment])

# ────────────────────────────────────────────────────────────────────────────────
# 4.  Persona filtering & three‑column grid
# ────────────────────────────────────────────────────────────────────────────────
filtered_personas: list[dict] = []
for group in persona_data:
    if selected_segment == "All" or group["segment"] == selected_segment:
        for gender in ("male", "female"):
            if (persona := group.get(gender)):
                filtered_personas.append({"persona": persona, "segment": group["segment"]})

st.markdown("## 👥 Select a Persona")
cols = st.columns([1, 1, 1], gap="small")  # 👈 avoids collapse on small screens

for i, entry in enumerate(filtered_personas):
    with cols[i % 3]:
        p = entry["persona"]
        if (img := p.get("image")):
            st.image(img, caption=p["name"], use_container_width=True)
        st.markdown(f"### {p['name']}")
        st.markdown(f"*{entry['segment']}*")
        st.markdown(f"📍 {p.get('location','')}  ")
        st.markdown(f"🎂 {p.get('age','')} years old")
        if st.button("Select", key=f"select_{i}"):
            st.session_state.selected_persona = p
            st.session_state.selected_segment = entry["segment"]

# ────────────────────────────────────────────────────────────────────────────────
# 5.  Selected persona summary card
# ────────────────────────────────────────────────────────────────────────────────
if "selected_persona" in st.session_state:
    persona = st.session_state.selected_persona
    segment = st.session_state.selected_segment

    summary_html = f"""
        <div style="background-color:#e3f6d8; padding:20px; border-left:6px solid #43B02A; border-radius:10px">
            <h4 style="margin-top:0;">{persona['name']} <span style="font-weight:normal;">({segment})</span></h4>
            <p><strong>Age:</strong> {persona.get('age')}</p>
            <p><strong>Location:</strong> {persona.get('location')}</p>
            <p><strong>Occupation:</strong> {persona.get('occupation')}</p>
            <p><strong>Income:</strong> ${persona.get('income'):,}</p>
            <p><strong>Risk Tolerance:</strong> {persona.get('behavioural_traits', {}).get('risk_tolerance')}</p>
            <p><strong>Goals:</strong><br>{''.join(f'• {g}<br>' for g in persona.get('goals', []))}</p>
            <p><strong>Values:</strong> {', '.join(persona.get('values', []))}</p>
            <p><strong>Narrative:</strong> {persona.get('narrative')}</p>
        </div>
    """
    st.markdown("---", unsafe_allow_html=True)
    st.markdown(summary_html, unsafe_allow_html=True)

    # Suggested questions
    st.markdown("### 💡 Suggested Questions")
    if persona.get("suggestions"):
        for s in persona["suggestions"]:
            if st.button(s):
                st.session_state.question_input = s
    else:
        st.markdown("*No suggested questions available for this persona.*")

# ────────────────────────────────────────────────────────────────────────────────
# 6.  LLM wrapper with caching + history update
# ────────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _generate_response(prompt: str):
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are simulating an investor responding in a realistic, conversational tone."},
            {"role": "user", "content": prompt},
        ],
    )
    return completion.choices[0].message.content.strip()


def ask_persona(persona_key: str, prompt: str):
    answer = _generate_response(prompt)
    st.session_state.chat_history.setdefault(persona_key, []).append((question, answer))
    return answer

# ────────────────────────────────────────────────────────────────────────────────
# 7.  Q&A interaction section
# ────────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("## 💬 Ask a Question")
question = st.text_area("Enter your question:", value=st.session_state.get("question_input", ""))
ask_all = st.checkbox("Ask All Personas")

if st.button("Ask GPT"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Contacting personas…"):
            try:
                # Handle ASK‑ALL scenario
                if ask_all:
                    for entry in filtered_personas:
                        p = entry["persona"]
                        prompt = (
                            f"You are {p['name']}, a {p['age']}-year-old {p['occupation']} from {p['location']}. "
                            f"Values: {', '.join(p['values'])}. You're asked: '{question}'\n\nHow do you respond?"
                        )
                        reply = ask_persona(p["name"], prompt)
                else:
                    persona = st.session_state.get("selected_persona")
                    if persona is None:
                        st.warning("Please select a persona.")
                        st.stop()
                    prompt = (
                        f"You are {persona['name']}, a {persona['age']}-year-old {persona['occupation']} from {persona['location']}. "
                        f"Values: {', '.join(persona['values'])}. You're asked: '{question}'\n\nHow do you respond?"
                    )
                    reply = ask_persona(persona["name"], prompt)
            except Exception as e:
                st.error(f"Error: {e}")

# ────────────────────────────────────────────────────────────────────────────────
# 8.  Render chat history bubbles
# ────────────────────────────────────────────────────────────────────────────────

if st.session_state.chat_history:
    st.markdown("---")
    st.markdown("### 🗂️ Conversation History")
    for persona_key, exchanges in st.session_state.chat_history.items():
        st.markdown(f"#### {persona_key}")
        for q, a in exchanges:
            st.markdown(f"<div style='background:#fafafa; padding:8px 12px; border-left:4px solid #485cc7; border-radius:4px;'><strong>You:</strong> {q}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background:#e3f6d8; padding:8px 12px; border-left:4px solid #43B02A; border-radius:4px;'><strong>{persona_key}:</strong> {a}</div>", unsafe_allow_html=True)
            st.markdown("&nbsp;")
