import streamlit as st
import db.recipes as recipes_db
from db.client import get_client


def get_title() -> str:
    recipe_id = st.query_params.get("id")
    if not recipe_id:
        return "Receta"
    res = get_client().table("recipes").select("title").eq("id", recipe_id).single().execute()
    return res.data["title"] if res.data else "Receta"


def render():
    recipe_id = st.query_params.get("id")
    if not recipe_id:
        st.error("Receta no encontrada.")
        return

    recipe = recipes_db.get_by_id(recipe_id)
    if not recipe:
        st.error("Receta no encontrada.")
        return

    # ── Acciones ───────────────────────────────────────────────
    _, col_actions = st.columns([5, 1])
    with col_actions:
        if st.button("✏️ Editar"):
            st.query_params["page"] = "edit"
            st.query_params["id"] = recipe_id
            st.rerun()
        if st.button("🗑️ Eliminar"):
            st.session_state._confirm_delete = True

    if st.session_state.get("_confirm_delete"):
        st.warning("¿Seguro que querés eliminar esta receta?")
        c1, c2 = st.columns([1, 5])
        if c1.button("Sí, eliminar", type="primary"):
            recipes_db.delete(recipe_id)
            st.session_state._confirm_delete = False
            st.query_params["page"] = "home"
            st.rerun()
        if c2.button("Cancelar"):
            st.session_state._confirm_delete = False
            st.rerun()

    if recipe.get("description"):
        st.write(recipe["description"])

    # ── Tiempo y porciones ─────────────────────────────────────
    col_time, col_serv = st.columns(2)
    if recipe.get("cook_time"):
        col_time.metric("Tiempo", f"{recipe['cook_time']} min")
    if recipe.get("servings"):
        col_serv.metric("Porciones", recipe["servings"])

    # ── Tags ───────────────────────────────────────────────────
    tags = [rt["tags"] for rt in recipe.get("tags", []) if rt.get("tags")]
    if tags:
        st.write(" ".join(f"`{t['name']}`" for t in tags))

    st.divider()

    # ── Ingredientes con escalado ──────────────────────────────
    st.subheader("Ingredientes")

    original_servings = recipe.get("servings") or 0
    scale = 1.0
    if original_servings > 0:
        target = st.number_input(
            "Porciones",
            min_value=1,
            value=original_servings,
            step=1,
            help="Cambiá las porciones para escalar las cantidades",
        )
        scale = target / original_servings

    ingredients = recipe.get("ingredients", [])
    if ingredients:
        for ing in ingredients:
            name = ing["ingredients"]["name"]
            qty = ing.get("quantity")
            unit = ing.get("units")

            if qty:
                scaled = qty * scale
                # Muestra entero si no tiene decimales significativos
                qty_str = str(int(scaled)) if scaled == int(scaled) else f"{scaled:.1f}"
                unit_str = f" {unit['abbreviation']}" if unit else ""
                st.write(f"- **{qty_str}{unit_str}** {name}")
            else:
                st.write(f"- {name}")
    else:
        st.write("_Sin ingredientes cargados._")

    st.divider()

    # ── Pasos ──────────────────────────────────────────────────
    st.subheader("Pasos")
    steps = recipe.get("steps", [])
    if steps:
        for step in steps:
            st.markdown(f"**{step['step_number']}.** {step['description']}")
            st.write("")
    else:
        st.write("_Sin pasos cargados._")

    # ── Volver ─────────────────────────────────────────────────
    st.divider()
    if st.button("← Volver"):
        st.query_params["page"] = "home"
        st.rerun()
