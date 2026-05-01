import io
import json
import os

import streamlit as st

import db.ingredients as ingredients_db
import db.units as units_db

_NEW_PREFIX = "__new__"


def get_title() -> str:
    return "Receta por audio"


def render():
    if st.button("← Volver"):
        st.query_params["page"] = "home"
        st.rerun()

    st.write("Contá la receta en voz y la app la transcribe y carga automáticamente.")

    tab_grabar, tab_subir = st.tabs(["🎙️ Grabar", "📁 Subir archivo"])

    audio_bytes = None

    with tab_grabar:
        from audio_recorder_streamlit import audio_recorder
        st.caption("Presioná el ícono para grabar, otra vez para detener.")
        recorded = audio_recorder(text="", icon_size="2x", neutral_color="#20264F", recording_color="#e63946")
        if recorded and recorded != st.session_state.get("_last_recorded"):
            st.session_state._last_recorded = recorded
            audio_bytes = recorded
            st.session_state.audio_raw = ("recording.wav", recorded)
            st.session_state.pop("audio_transcript", None)
            st.session_state.pop("audio_extracted", None)

    with tab_subir:
        uploaded = st.file_uploader(
            "Audio",
            type=["mp3", "wav", "m4a", "ogg", "webm"],
            label_visibility="collapsed",
        )
        if uploaded:
            raw = uploaded.read()
            if raw != st.session_state.get("_last_uploaded"):
                st.session_state._last_uploaded = raw
                st.session_state.audio_raw = (uploaded.name, raw)
                st.session_state.pop("audio_transcript", None)
                st.session_state.pop("audio_extracted", None)

    if "audio_raw" in st.session_state:
        fname, raw = st.session_state.audio_raw
        st.audio(raw)
        if st.button("Transcribir", type="primary"):
            with st.spinner("Transcribiendo..."):
                try:
                    transcript = _transcribe_bytes(raw, fname)
                    st.session_state.audio_transcript = transcript
                    st.session_state.pop("audio_extracted", None)
                except Exception as e:
                    st.error(f"Error al transcribir: {e}")
                    return
            st.rerun()

    if "audio_transcript" in st.session_state:
        transcript = st.text_area(
            "Transcripción (podés editarla antes de extraer)",
            value=st.session_state.audio_transcript,
            height=180,
            key="audio_transcript_edit",
        )

        if st.button("Extraer receta", type="primary"):
            with st.spinner("Extrayendo receta con IA..."):
                try:
                    extracted = _extract_recipe(transcript)
                    st.session_state.audio_extracted = extracted
                except Exception as e:
                    st.error(f"Error al extraer: {e}")
                    return
            st.rerun()

    if "audio_extracted" in st.session_state:
        st.divider()
        _show_preview(st.session_state.audio_extracted)
        st.divider()
        if st.button("Cargar al formulario →", type="primary"):
            with st.spinner("Cargando..."):
                _prefill_form(st.session_state.audio_extracted)
            st.query_params["page"] = "create"
            st.rerun()


# ── Whisper ────────────────────────────────────────────────────

def _transcribe_bytes(raw: bytes, filename: str) -> str:
    from openai import OpenAI

    key = os.getenv("OPENAI_API_KEY")
    if not key:
        try:
            key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            pass

    client = OpenAI(api_key=key)
    audio = io.BytesIO(raw)
    audio.name = filename

    result = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio,
        language="es",
    )
    return result.text


# ── GPT-4o-mini ────────────────────────────────────────────────

def _extract_recipe(transcript: str) -> dict:
    from openai import OpenAI

    key = os.getenv("OPENAI_API_KEY")
    if not key:
        try:
            key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            pass

    client = OpenAI(api_key=key)

    prompt = f"""El usuario dictó una receta de cocina. Transcripción:

\"\"\"{transcript}\"\"\"

Extraé la información y devolvé SOLO un JSON válido (sin bloques de markdown) con esta estructura exacta:
{{
  "title": "nombre de la receta",
  "description": "descripción breve o null",
  "cook_time": 30,
  "servings": 4,
  "ingredients": [
    {{"name": "harina", "quantity": 2.0, "unit": "taza"}}
  ],
  "steps": ["Mezclar bien.", "Hornear 30 minutos."]
}}

Reglas:
- Si no se menciona un campo de texto, usá null.
- Si no se menciona cook_time o servings, usá 0.
- Si no se menciona la unidad de un ingrediente, usá null en ese campo.
- quantity siempre debe ser un número (0 si no se menciona).
- steps debe ser una lista de strings, uno por paso."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1024,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )

    return json.loads(response.choices[0].message.content)


# ── Preview ────────────────────────────────────────────────────

def _show_preview(extracted: dict):
    st.subheader(extracted.get("title") or "Sin título")
    if extracted.get("description"):
        st.caption(extracted["description"])

    c1, c2 = st.columns(2)
    if extracted.get("cook_time"):
        c1.metric("Tiempo", f"{extracted['cook_time']} min")
    if extracted.get("servings"):
        c2.metric("Porciones", extracted["servings"])

    ingredients = extracted.get("ingredients") or []
    if ingredients:
        st.write("**Ingredientes:**")
        for ing in ingredients:
            qty = ing.get("quantity") or ""
            unit = ing.get("unit") or ""
            parts = [str(qty) if qty else "", unit, ing.get("name", "")]
            st.write("• " + " ".join(p for p in parts if p))

    steps = extracted.get("steps") or []
    if steps:
        st.write("**Pasos:**")
        for i, step in enumerate(steps, 1):
            st.write(f"{i}. {step}")


# ── Pre-carga del formulario ───────────────────────────────────

def _prefill_form(extracted: dict):
    all_ingredients = ingredients_db.get_all()
    all_units = units_db.get_all()

    st.session_state.f_title = extracted.get("title") or ""
    st.session_state.f_description = extracted.get("description") or ""
    st.session_state.f_tiempo = int(extracted.get("cook_time") or 0)
    st.session_state.f_servings = int(extracted.get("servings") or 0)
    st.session_state.f_tag_ids = []

    ing_keys = []
    counter = 0
    for ing_data in (extracted.get("ingredients") or []):
        name = (ing_data.get("name") or "").strip()
        if not name:
            continue
        matched = _match_ingredient(name, all_ingredients)
        if matched:
            ing_tuple = matched
        else:
            new_ing = ingredients_db.create(name)
            all_ingredients.append(new_ing)
            ing_tuple = (new_ing["name"], new_ing["id"])

        st.session_state[f"ing_search_{counter}"] = ing_tuple
        st.session_state[f"ing_qty_{counter}"] = float(ing_data.get("quantity") or 0)
        st.session_state[f"ing_unit_{counter}"] = _match_unit(ing_data.get("unit") or "", all_units)
        ing_keys.append(counter)
        counter += 1

    if not ing_keys:
        st.session_state["ing_search_0"] = None
        st.session_state["ing_qty_0"] = 0.0
        st.session_state["ing_unit_0"] = None
        ing_keys = [0]
        counter = 1

    st.session_state.f_ing_keys = ing_keys
    st.session_state._f_ing_counter = counter

    step_keys = []
    step_counter = 0
    for step in (extracted.get("steps") or []):
        if step.strip():
            st.session_state[f"step_desc_{step_counter}"] = step.strip()
            step_keys.append(step_counter)
            step_counter += 1

    if not step_keys:
        st.session_state["step_desc_0"] = ""
        step_keys = [0]
        step_counter = 1

    st.session_state.f_step_keys = step_keys
    st.session_state._f_step_counter = step_counter

    # Marcar como cargado para que _init_state no sobreescriba el estado
    st.session_state._f_loaded = "new"


def _match_ingredient(name: str, all_ingredients: list) -> tuple | None:
    name_l = name.lower()
    for ing in all_ingredients:
        if ing["name"].lower() == name_l:
            return (ing["name"], ing["id"])
    for ing in all_ingredients:
        if name_l in ing["name"].lower() or ing["name"].lower() in name_l:
            return (ing["name"], ing["id"])
    return None


def _match_unit(unit_name: str, all_units: list) -> str | None:
    if not unit_name:
        return None
    u_l = unit_name.lower().strip()
    for u in all_units:
        if u["name"].lower() == u_l or u["abbreviation"].lower() == u_l:
            return u["id"]
    return None
