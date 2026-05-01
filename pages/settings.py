import streamlit as st
import db.tags as tags_db
import db.units as units_db
import db.ingredients as ingredients_db


def get_title() -> str:
    return "Configuración"


def render():
    if st.button("← Volver"):
        st.query_params["page"] = "home"
        st.rerun()

    tab_tags, tab_units, tab_ingredients = st.tabs(["Tags", "Unidades", "Ingredientes"])

    # ── Tags ───────────────────────────────────────────────────
    with tab_tags:
        tag_types = tags_db.get_all_types()
        all_tags = tags_db.get_all()
        type_map = {tt["id"]: tt["name"] for tt in tag_types}

        st.subheader("Tipos de tag")
        with st.form("new_tag_type"):
            c1, c2 = st.columns([4, 1])
            new_type_name = c1.text_input("Nuevo tipo", label_visibility="collapsed", placeholder="Ej: Proteína, Ocasión...")
            if c2.form_submit_button("Agregar") and new_type_name.strip():
                tags_db.create_type(new_type_name)
                st.rerun()

        for tt in tag_types:
            _editable_row(
                label=tt["name"],
                on_save=lambda name, id=tt["id"]: tags_db.update_type(id, name),
                on_delete=lambda id=tt["id"]: tags_db.delete_type(id),
                edit_key=f"edit_type_{tt['id']}",
                delete_key=f"del_type_{tt['id']}",
                confirm_key=f"confirm_del_type_{tt['id']}",
            )

        st.divider()
        st.subheader("Tags")
        with st.form("new_tag"):
            c1, c2, c3 = st.columns([3, 2, 1])
            new_tag_name = c1.text_input("Nuevo tag", label_visibility="collapsed", placeholder="Ej: Pollo, Pasta...")
            selected_type = c2.selectbox(
                "Tipo", options=[None] + [tt["id"] for tt in tag_types],
                format_func=lambda x: "— sin tipo —" if x is None else type_map[x],
                label_visibility="collapsed",
            )
            if c3.form_submit_button("Agregar") and new_tag_name.strip():
                tags_db.create(new_tag_name, selected_type)
                st.rerun()

        for tag in all_tags:
            type_name = tag.get("tag_types", {}).get("name") if tag.get("tag_types") else "Sin tipo"
            _editable_row(
                label=f"{tag['name']} · *{type_name or 'Sin tipo'}*",
                on_save=lambda name, id=tag["id"]: tags_db.update_tag(id, name),
                on_delete=lambda id=tag["id"]: tags_db.delete_tag(id),
                edit_key=f"edit_tag_{tag['id']}",
                delete_key=f"del_tag_{tag['id']}",
                confirm_key=f"confirm_del_tag_{tag['id']}",
            )

    # ── Unidades ───────────────────────────────────────────────
    with tab_units:
        units = units_db.get_all()
        st.subheader("Unidades")
        with st.form("new_unit"):
            c1, c2, c3 = st.columns([3, 1, 1])
            new_unit_name = c1.text_input("Nombre", label_visibility="collapsed", placeholder="Ej: taza")
            new_unit_abbr = c2.text_input("Abrev.", label_visibility="collapsed", placeholder="taza")
            if c3.form_submit_button("Agregar") and new_unit_name.strip() and new_unit_abbr.strip():
                units_db.create(new_unit_name, new_unit_abbr)
                st.rerun()

        for u in units:
            _editable_row(
                label=f"{u['name']} ({u['abbreviation']})",
                on_save=lambda name, id=u["id"], abbr=u["abbreviation"]: units_db.update(id, name.split(" (")[0], abbr),
                on_delete=lambda id=u["id"]: units_db.delete(id),
                edit_key=f"edit_unit_{u['id']}",
                delete_key=f"del_unit_{u['id']}",
                confirm_key=f"confirm_del_unit_{u['id']}",
            )

    # ── Ingredientes ───────────────────────────────────────────
    with tab_ingredients:
        ingredients = ingredients_db.get_all()
        st.subheader("Catálogo de ingredientes")
        st.caption("También se pueden crear inline al cargar una receta.")

        with st.form("new_ingredient"):
            c1, c2 = st.columns([4, 1])
            new_ing_name = c1.text_input("Nuevo ingrediente", label_visibility="collapsed", placeholder="Ej: Harina de trigo")
            if c2.form_submit_button("Agregar") and new_ing_name.strip():
                ingredients_db.create(new_ing_name)
                st.rerun()

        for ing in ingredients:
            _editable_row(
                label=ing["name"],
                on_save=lambda name, id=ing["id"]: ingredients_db.update(id, name),
                on_delete=lambda id=ing["id"]: _safe_delete_ingredient(id),
                edit_key=f"edit_ing_{ing['id']}",
                delete_key=f"del_ing_{ing['id']}",
                confirm_key=f"confirm_del_ing_{ing['id']}",
            )


# ── Componente reutilizable: fila con editar / eliminar ────────

def _editable_row(label, on_save, on_delete, edit_key, delete_key, confirm_key):
    is_editing = st.session_state.get(edit_key, False)
    is_confirming = st.session_state.get(confirm_key, False)

    if is_editing:
        current_name = label.split(" ·")[0].split(" (")[0]
        c_input, c_save, c_cancel = st.columns([4, 1, 1])
        new_val = c_input.text_input("", value=current_name, key=f"val_{edit_key}", label_visibility="collapsed")
        if c_save.button("✓", key=f"save_{edit_key}") and new_val.strip():
            on_save(new_val.strip())
            st.session_state[edit_key] = False
            st.rerun()
        if c_cancel.button("✕", key=f"cancel_{edit_key}"):
            st.session_state[edit_key] = False
            st.rerun()
    elif is_confirming:
        c_label, c_yes, c_no = st.columns([4, 1, 1])
        c_label.markdown(f"~~{label}~~ ¿Eliminar?")
        if c_yes.button("Sí", key=f"yes_{confirm_key}", type="primary"):
            on_delete()
            st.session_state[confirm_key] = False
            st.rerun()
        if c_no.button("No", key=f"no_{confirm_key}"):
            st.session_state[confirm_key] = False
            st.rerun()
    else:
        c_label, c_edit, c_del = st.columns([4, 0.7, 0.7])
        c_label.markdown(label)
        if c_edit.button("✏️", key=f"btn_{edit_key}"):
            st.session_state[edit_key] = True
            st.rerun()
        if c_del.button("🗑️", key=f"btn_{delete_key}"):
            st.session_state[confirm_key] = True
            st.rerun()


def _safe_delete_ingredient(ingredient_id: str):
    try:
        ingredients_db.delete(ingredient_id)
    except Exception:
        st.error("No se puede eliminar: el ingrediente está en uso en alguna receta.")
