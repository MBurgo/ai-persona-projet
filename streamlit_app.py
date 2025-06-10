import streamlit as st
import json
from openai import OpenAI

# ────────────────────────────────────────────────────────────────────────────────
# Session‑state initialisation
# ────────────────────────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    # {persona_name|"ALL": [(question, answer), …]}
    st.session_state.chat_history: dict[str, list[tuple[str, str]]] = {}
if "question_input" not in st.session_state:
    st.session_state.question_input = ""

# ────────────────────────────────────────────────────────────────────────────────
# Load data & model client
# ────────────────────────────────────────────────────────────────────────────────
with open("personas.json", "r", encoding="utf-8") as f:
    persona_data = json.load(f)["personas"]

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

segment_summaries = {
    "Next Generation Investors (18–24 years)": "These young investors are tech‑savvy, socially conscious, and ambitious…",
    "Emerging Wealth Builders (25–34 years)": "These individuals are in the early stages of wealth accumulation…",
    "Established Accumulators (35–49 years)": "Often juggling career and family, these investors focus on financial security…",
    "Pre‑Retirees (50–64 years)": "Pre‑retirees are focused on preserving wealth, planning for a secure retirement…",
    "Retirees (65+ years)": "This segment prioritises stability, simplicity, and preserving capital…",
}

# ────────────────────────────────────────────────────────────────────────────────
# Streamlit UI setup
# ────────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Burgo's Persona Portal", layout="centered", page_icon="💬")

st.markdown(
    """<style>.stButton>button{border:1px solid #485cc7;border-radius:8px}</style>""",
    unsafe_allow_html=True,
)

st.title("🧠 Matt's Test Persona Portal")

st.markdown(
    """
    <div style="background:#f0f2f6;padding:20px;border-left:6px solid #485cc7;border-radius:10px;margin-bottom:25px">
        <h4 style="margin-top:0">ℹ️ About This Tool</h4>
    <p>This tool uses AI-generated investor personas — built from real Australian investor research — to simulate how different segments might respond to your ideas.</p>
    <p>Each persona is built on rich attributes — including goals, values, behaviours, concerns, and communication preferences — informed by real investor research such as the ASX Investor Study, Investment Trends reports, Stake member surveys, and more.</p>
    <p>GPT-4o is then used to emulate how these personas might realistically think, feel, and respond, based on their individual attributes.</p>
    <p>The goal? To give marketing and product teams a quick, easy way to test ideas and spark fresh thinking — without needing to run full-scale research.</p>
    <p>Of course, there are limitations. AI personas obviously aren’t real people. But they’re grounded in data, and designed to (hopefully) help inspire new ideas.</p>    </div>""",
    unsafe_allow_html=True,
)

st.markdown("Select a persona to view their profile, then ask questions to gauge reactions.")

# ────────────────────────────────────────────────────────────────────────────────
# Segment filter + overview accordion
# ────────────────────────────────────────────────────────────────────────────────
segments = sorted({p["segment"] for p in persona_data})
selected_segment = st.selectbox("Filter by Segment", ["All"] + segments)

if selected_segment == "All":
    with st.expander("🔍 Segment cheat‑sheet"):
        for seg, blurb in segment_summaries.items():
            st.markdown(f"**{seg}**  \n{blurb}\n")
else:
    with st.expander("🔍 Segment overview", expanded=True):
        st.write(segment_summaries[selected_segment])

# ────────────────────────────────────────────────────────────────────────────────
# Persona grid
# ────────────────────────────────────────────────────────────────────────────────
filtered_personas = []
for group in persona_data:
    if selected_segment == "All" or group["segment"] == selected_segment:
        for gender in ("male", "female"):
            if (persona := group.get(gender)):
                filtered_personas.append({"persona": persona, "segment": group["segment"]})

st.markdown("## 👥 Select a Persona")
cols = st.columns([1, 1, 1], gap="small")
for i, entry in enumerate(filtered_personas):
    p = entry["persona"]
    with cols[i % 3]:
        if (img := p.get("image")):
            st.image(img, caption=p["name"], use_container_width=True)
        st.markdown(f"### {p['name']}")
        st.markdown(f"*{entry['segment']}*")
        st.markdown(f"📍 {p.get('location','')}")
        st.markdown(f"🎂 {p.get('age','')} years old")
        if st.button("Select", key=f"sel_{i}"):
            st.session_state.selected_persona = p
            st.session_state.selected_segment = entry["segment"]

# ────────────────────────────────────────────────────────────────────────────────
# Persona profile
# ────────────────────────────────────────────────────────────────────────────────
if "selected_persona" in st.session_state:
    persona = st.session_state.selected_persona
    seg = st.session_state.selected_segment

    st.markdown("---")
    st.markdown(
        f"""
        <div style="background:#e3f6d8;padding:20px;border-left:6px solid #43B02A;border-radius:10px">
            <h4 style="margin-top:0">{persona['name']} <span style="font-weight:normal">({seg})</span></h4>
            <p><strong>Age:</strong> {persona.get('age')}</p>
            <p><strong>Location:</strong> {persona.get('location')}</p>
            <p><strong>Occupation:</strong> {persona.get('occupation')}</p>
            <p><strong>Income:</strong> ${persona.get('income'):,}</p>
            <p><strong>Risk Tolerance:</strong> {persona.get('behavioural_traits', {}).get('risk_tolerance')}</p>
            <p><strong>Goals:</strong><br>{''.join('• '+g+'<br>' for g in persona.get('goals', []))}</p>
            <p><strong>Values:</strong> {', '.join(persona.get('values', []))}</p>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown("### 💡 Suggested Questions")
    if persona.get("suggestions"):
        for s in persona["suggestions"]:
            if st.button(s):
                st.session_state.question_input = s
    else:
        st.markdown("*No suggestions for this persona.*")

# ────────────────────────────────────────────────────────────────────────────────
# Helper: build ChatCompletion messages with memory
# ────────────────────────────────────────────────────────────────────────────────

def build_messages(persona_intro: str, history: list[tuple[str, str]], new_q: str):
    """Convert prior Q&A into role‑alternating messages (max last 4 turns)."""
    msgs = [
        {"role": "system", "content": "You are simulating an investor responding in a realistic, conversational tone."},
        {"role": "user", "content": persona_intro},
    ]
    for q, a in history[-4:]:
        msgs.extend([
            {"role": "user", "content": q},
            {"role": "assistant", "content": a},
        ])
    msgs.append({"role": "user", "content": new_q})
    return msgs

# Cached LLM call --------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _ask_llm(messages: list):
    reply = client.chat.completions.create(model="o3", messages=messages)
    return reply.choices[0].message.content.strip()

# Ask‑persona wrapper -----------------------------------------------------------

def ask_persona(persona: dict, question: str):
    name = persona["name"]
    intro = (
        f"You are {name}, a {persona['age']}-year‑old {persona['occupation']} from {persona['location']}. "
        f"Your values: {', '.join(persona['values'])}. Respond as this individual." )
    hist = st.session_state.chat_history.get(name, [])
    answer = _ask_llm(build_messages(intro, hist, question))
    st.session_state.chat_history.setdefault(name, []).append((question, answer))
    return answer

# ────────────────────────────────────────────────────────────────────────────────
# Q&A Section
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
                if ask_all:
                    for ent in filtered_personas:
                        reply = ask_persona(ent["persona"], question)
                else:
                    if "selected_persona" not in st.session_state:
                        st.warning("Please select a persona.")
                        st.stop()
                    reply = ask_persona(st.session_state.selected_persona, question)
            except Exception as e:
                st.error(f"Error: {e}")

# ────────────────────────────────────────────────────────────────────────────────
# Conversation history display
# ────────────────────────────────────────────────────────────────────────────────

if st.session_state.chat_history:
    st.markdown("---")
    st.markdown("### 🗂️ Conversation History")
    for persona_name, exchanges in st.session_state.chat_history.items():
        st.markdown(f"#### {persona_name}")
        for q, a in exchanges:
            st.markdown(f"<div style='background:#fafafa;padding:8px;border-left:4px solid #485cc7;border-radius:4px'><strong>You:</strong> {q}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background:#e3f6d8;padding:8px;border-left:4px solid #43B02A;border-radius:4px'><strong>{persona_name}:</strong> {a}</div>", unsafe_allow_html=True)
            st.markdown("&nbsp;")
