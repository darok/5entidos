import streamlit as st
from pathlib import Path
import base64

def _img_to_base64(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode()

st.set_page_config(
    page_title="5entidos",
    page_icon="resources/logo_icon.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS global ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Nunito', sans-serif;
}

/* Cards de recetas */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px !important;
    border-color: #BCC0DD !important;
    transition: box-shadow 0.2s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 4px 16px rgba(32, 38, 79, 0.12) !important;
}

/* Botón primario */
div[data-testid="stButton"] > button[kind="primary"] {
    background-color: #20264F;
    border-radius: 8px;
    font-weight: 700;
    letter-spacing: 0.3px;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    background-color: #2E3668;
    border-color: #2E3668;
}

/* Botones secundarios */
div[data-testid="stButton"] > button {
    border-radius: 8px;
}

/* Inputs */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stNumberInput"] input {
    border-radius: 8px;
}

/* Dividers */
hr {
    border-color: #BCC0DD;
    opacity: 0.5;
}

/* Ocultar sidebar y hamburger — navegación propia */
[data-testid="stSidebar"],
[data-testid="collapsedControl"] {
    display: none !important;
}

/* Reducir padding lateral en mobile */
.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
}

/* Header: logo + título de página */
.app-header {
    display: flex;
    align-items: center;
    gap: 24px;
    padding: 24px 0 20px 0;
    border-bottom: 2px solid #BCC0DD;
    margin-bottom: 28px;
}
.app-header img {
    height: 150px;
    width: auto;
}
.app-header-title {
    font-family: 'Nunito', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: #20264F;
    line-height: 1.1;
}
</style>
""", unsafe_allow_html=True)

# ── Navegación via query param ?page= ─────────────────────────
page = st.query_params.get("page", "home")

if page == "home":
    from pages.home import render, get_title
elif page == "recipe":
    from pages.recipe_detail import render, get_title
elif page == "create":
    from pages.create_edit_recipe import render, get_title
elif page == "edit":
    from pages.create_edit_recipe import render, get_title
elif page == "settings":
    from pages.settings import render, get_title
elif page == "audio":
    from pages.audio_recipe import render, get_title
else:
    from pages.home import render, get_title

# ── Header: logo + título de página ───────────────────────────
logo_b64 = _img_to_base64("resources/logo_full.png")
st.markdown(f"""
<div class="app-header">
    <img src="data:image/png;base64,{logo_b64}" />
    <span class="app-header-title">{get_title()}</span>
</div>
""", unsafe_allow_html=True)

render()
