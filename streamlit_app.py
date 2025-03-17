import streamlit as st
import json
import requests

# Get API key from Streamlit secrets
api_key = st.secrets["OPENAI_API_KEY"]

# Load persona data
with open("personas.json") as f:
    persona_data = json.load(f)["personas"]

# Segment summaries based on aggregated traits
segment_summaries = {
    "Next Generation Investors (18–24 years)": "These young investors are tech-savvy, socially conscious, and ambitious. They seek financial independence, value creativity and personal freedom, and are primarily influenced by peers and social media trends. Their risk tolerance is generally high, and they prefer platforms that are interactive and visually engaging.",
    "Emerging Wealth Builders (25–34 years)": "These individuals are in the early stages of wealth accumulation, often with moderate to high investing experience. They are ambitious and analytical, driven by goals like starting a business, financial freedom, and buying a home. They value innovation, entrepreneurship, and sustainability, and tend to be comfortable with moderate to high risk in pursuit of growth.",
    "Established Accumulators (35–49 years)": "Often juggling career and family, these investors focus on financial security and long-term planning. They are pragmatic and goal-oriented, aiming to fund children’s education, grow wealth, and prepare for retirement. They seek expert advice and tend to have a moderate risk tolerance, balancing growth with asset protection.",
    "Pre-Retirees (50–64 years)": "Pre-retirees are focused on preserving wealth, planning for a secure retirement, and leaving a legacy. They are typically analytical, cautious, and value expert guidance. Stability and income generation are top priorities, and they often consult multiple professionals before making decisions. Risk tolerance is generally low to moderate.",
    "Retirees (65+ years)": "This segment prioritises stability, simplicity, and preserving capital. Most are retired professionals who rely on trusted advisors and conservative investments to support their lifestyle and family. Their values include family, integrity, and community, and they prefer face-to-face services and clear, jargon-free information. Their risk tolerance is low."
}

# App configuration
st.set_page_config(page_title="Persona Portal", layout="centered")
st.title("🧠 Matt's Test Persona Portal")
st.markdown("""
Welcome to the Persona Portal! This tool allows you to interact with various investing personas. Select a persona to view their profile and ask them questions to gain insights into different investor perspectives.
""")

# Segment filter
segments = sorted(set(p["segment"] for p in persona_data))
selected_segment = st.selectbox("Filter by Segment", ["All"] + segments)

# Show segment summary
if selected_segment in segment_summaries:
    st.info(segment_summaries[selected_segment])

# Filter personas
filtered_personas = []
for group in persona_data:
    if selected_segment == "All" or group["segment"] == selected_segment:
        for gender in ["male", "female"]:
            persona = group.get(gender)
            if persona:
                filtered_personas.append({
                    "persona": persona,
                    "segment": group["segment"]
                })

# Persona grid display
st.markdown("## 👥 Select a Persona")
cols = st.columns(3)
selected_index = None
for i, entry in enumerate(filtered_personas):
    with cols[i % 3]:
        image_url = entry["persona"].get("image")
        if image_url:
            st.image(image_url, use_container_width=True)
        st.markdown(f"### {entry['persona']['name']}")
        st.markdown(f"*{entry['segment']}*  ")
        st.markdown(f"📍 {entry['persona'].get('location', '')}  ")
        st.markdown(f"🎂 {entry['persona'].get('age', '')} years old")
        if st.button("Select", key=f"select_{i}"):
            selected_index = i
            st.session_state.selected_persona = entry["persona"]
            st.session_state.selected_segment = entry["segment"]

# Display selected persona summary
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
        <p><strong>Goals:</strong><br>{"".join(f"• {goal}<br>" for goal in persona.get("goals", []))}</p>
        <p><strong>Values:</strong> {", ".join(persona.get("values", []))}</p>
        <p><strong>Narrative:</strong> {persona.get("narrative")}</p>
    </div>
    """

    st.markdown("---", unsafe_allow_html=True)
    st.markdown(summary_html, unsafe_allow_html=True)

    # Suggested questions
    st.markdown("### 💡 Suggested Questions")
    if persona.get("suggestions"):
        for suggestion in persona["suggestions"]:
            if st.button(suggestion):
                st.session_state.question_input = suggestion
    else:
        st.markdown("*No suggested questions available for this persona.*")

# Ask question
st.markdown("---")
st.markdown("## 💬 Ask a Question")
question = st.text_area("Enter your question:", value=st.session_state.get("question_input", ""))
ask_all = st.checkbox("Ask All Personas")

if st.button("Ask GPT"):
    if not question:
        st.warning("Please enter a question.")
    else:
        with st.spinner("Contacting personas..."):
            payload = {
                "question": question,
                "askAll": ask_all
            }
            if not ask_all:
                payload["persona"] = st.session_state.get("selected_persona")
                payload["segment"] = st.session_state.get("selected_segment")
            try:
                # 🔁 Update this endpoint if needed for production
                res = requests.post("http://localhost:5000/test-gpt", json=payload, headers={"Authorization": f"Bearer {api_key}"})
                res.raise_for_status()
                response_data = res.json()
                if ask_all:
                    for entry in response_data.get("responses", []):
                        st.markdown(f"**{entry['name']} ({entry['segment']}):**  ")
                        st.markdown(entry['response'])
                        st.markdown("---")
                else:
                    st.markdown(response_data.get("response", "No response received."))
            except Exception as e:
                st.error(f"Error: {e}")
