import streamlit as st
import db.recipes as recipes_db
import db.tags as tags_db


def get_title() -> str:
    return "Mis recetas"

def render():
    _, col_nueva, col_audio, col_config = st.columns([4, 1, 1, 1])
    if col_nueva.button("＋ Nueva", type="primary", use_container_width=True):
        st.session_state._f_loaded = None
        st.query_params["page"] = "create"
        st.rerun()
    if col_audio.button("🎙️ Audio", use_container_width=True):
        st.query_params["page"] = "audio"
        st.rerun()
    if col_config.button("⚙️ Config", use_container_width=True):
        st.query_params["page"] = "settings"
        st.rerun()

    all_recipes = recipes_db.get_all()
    all_tags = tags_db.get_all()

    # ── Filtros ────────────────────────────────────────────────
    col_search, col_tags = st.columns([2, 3])
    search = col_search.text_input("Buscar", placeholder="Buscar por nombre...", label_visibility="collapsed")
    tag_map = {t["id"]: t["name"] for t in all_tags}
    selected_tags = col_tags.multiselect(
        "Filtrar por tags",
        options=list(tag_map.keys()),
        format_func=lambda x: tag_map[x],
        label_visibility="collapsed",
        placeholder="Filtrar por tags...",
    )

    # ── Filtrado en cliente (100-200 recetas, no requiere server) ──
    recipes = all_recipes
    if search:
        recipes = [r for r in recipes if search.lower() in r["title"].lower()]
    if selected_tags:
        selected_set = set(selected_tags)
        recipes = [
            r for r in recipes
            if selected_set & {rt["tag_id"] for rt in r.get("recipe_tags", [])}
        ]

    st.write(f"{len(recipes)} receta{'s' if len(recipes) != 1 else ''}")
    st.divider()

    if not recipes:
        st.info("No hay recetas que coincidan." if (search or selected_tags) else "Todavía no cargaste ninguna receta.")
        return

    # ── Grid de recetas (3 columnas) ───────────────────────────
    cols = st.columns(3)
    for i, recipe in enumerate(recipes):
        with cols[i % 3]:
            _recipe_card(recipe, tag_map)


def _recipe_card(recipe: dict, tag_map: dict):
    with st.container(border=True):
        if st.button(recipe["title"], key=f"card_{recipe['id']}", use_container_width=True):
            st.query_params["page"] = "recipe"
            st.query_params["id"] = recipe["id"]
            st.rerun()

        # Tiempos
        parts = []
        if recipe.get("cook_time"):
            parts.append(f"⏱ {recipe['cook_time']} min")
        if recipe.get("servings"):
            parts.append(f"🍽 {recipe['servings']} porc.")
        if parts:
            st.caption(" · ".join(parts))

        # Tags
        tags = [rt["tags"] for rt in recipe.get("recipe_tags", []) if rt.get("tags")]
        if tags:
            st.write(" ".join(f"`{t['name']}`" for t in tags))
