import streamlit as st
from streamlit_searchbox import st_searchbox
import db.recipes as recipes_db
import db.ingredients as ingredients_db
import db.units as units_db
import db.tags as tags_db

_NEW_PREFIX = "__new__"


def get_title() -> str:
    is_edit = st.query_params.get("page") == "edit" and bool(st.query_params.get("id"))
    return "Editar receta" if is_edit else "Nueva receta"

def render():
    page = st.query_params.get("page", "create")
    recipe_id = st.query_params.get("id")
    is_edit = page == "edit" and bool(recipe_id)

    ingredients = ingredients_db.get_all()
    units = units_db.get_all()
    tags = tags_db.get_all()

    _init_state(recipe_id if is_edit else None)

    # ── Datos básicos ──────────────────────────────────────────
    st.text_input("Título", key="f_title", placeholder="Nombre de la receta")
    st.text_area("Descripción", key="f_description", placeholder="Descripción breve (opcional)")

    c1, c2 = st.columns(2)
    c1.number_input("Tiempo (min)", min_value=0, step=5, key="f_tiempo")
    c2.number_input("Porciones", min_value=0, step=1, key="f_servings")

    # ── Ingredientes ───────────────────────────────────────────
    st.subheader("Ingredientes")
    _render_ingredient_rows(ingredients, units)

    # ── Pasos ──────────────────────────────────────────────────
    st.subheader("Pasos")
    _render_step_rows()

    # ── Tags ───────────────────────────────────────────────────
    st.subheader("Tags")
    tag_map = {t["id"]: t["name"] for t in tags}
    st.multiselect(
        "Tags",
        options=list(tag_map.keys()),
        format_func=lambda x: tag_map[x],
        key="f_tag_ids",
        label_visibility="collapsed",
    )

    st.divider()
    col_save, col_cancel, _ = st.columns([1, 1, 5])
    if col_save.button("Guardar", type="primary"):
        _save(recipe_id if is_edit else None, ingredients)
    if col_cancel.button("Cancelar"):
        st.query_params["page"] = "home"
        st.rerun()


# ── Inicialización del estado del formulario ───────────────────

def _init_state(recipe_id: str | None):
    # Solo inicializa en la primera carga o al cambiar de receta
    loaded_key = recipe_id or "new"
    if st.session_state.get("_f_loaded") == loaded_key:
        return

    st.session_state._f_loaded = loaded_key
    st.session_state._f_ing_counter = 0
    st.session_state._f_step_counter = 0

    if recipe_id:
        recipe = recipes_db.get_by_id(recipe_id)
        st.session_state.f_title = recipe["title"]
        st.session_state.f_description = recipe.get("description") or ""
        st.session_state.f_tiempo = recipe.get("cook_time") or 0
        st.session_state.f_servings = recipe.get("servings") or 0
        st.session_state.f_tag_ids = [rt["tag_id"] for rt in recipe.get("tags", [])]

        ing_keys = []
        for ing in recipe.get("ingredients", []):
            k = st.session_state._f_ing_counter
            # st_searchbox espera una tupla (label, value) como valor inicial
            ing_name = ing.get("ingredients", {}).get("name", "")
            st.session_state[f"ing_search_{k}"] = (ing_name, ing["ingredient_id"])
            st.session_state[f"ing_qty_{k}"] = float(ing.get("quantity") or 0)
            st.session_state[f"ing_unit_{k}"] = ing.get("unit_id")
            ing_keys.append(k)
            st.session_state._f_ing_counter += 1
        st.session_state.f_ing_keys = ing_keys

        step_keys = []
        for step in recipe.get("steps", []):
            k = st.session_state._f_step_counter
            st.session_state[f"step_desc_{k}"] = step["description"]
            step_keys.append(k)
            st.session_state._f_step_counter += 1
        st.session_state.f_step_keys = step_keys
    else:
        st.session_state.f_title = ""
        st.session_state.f_description = ""
        st.session_state.f_tiempo = 0
        st.session_state.f_servings = 0
        st.session_state.f_tag_ids = []
        st.session_state.f_ing_keys = [0]
        st.session_state.f_step_keys = [0]
        st.session_state._f_ing_counter = 1
        st.session_state._f_step_counter = 1


# ── Sección de ingredientes ────────────────────────────────────

def _make_search_fn(all_ingredients: list):
    # Devuelve opciones filtradas; si no hay match agrega "Crear X"
    def search(term: str) -> list[tuple[str, str]]:
        term = term.strip()
        if not term:
            return [(i["name"], i["id"]) for i in all_ingredients]
        matches = [(i["name"], i["id"]) for i in all_ingredients if term.lower() in i["name"].lower()]
        if not matches:
            matches = [(f"➕ Crear '{term}'", f"{_NEW_PREFIX}{term}")]
        return matches
    return search

def _render_ingredient_rows(ingredients: list, units: list):
    unit_map = {u["id"]: f"{u['name']} ({u['abbreviation']})" for u in units}
    unit_options = [None] + [u["id"] for u in units]
    search_fn = _make_search_fn(ingredients)

    to_remove = None

    for k in st.session_state.f_ing_keys:
        c_ing, c_qty, c_unit, c_rm = st.columns([3, 1, 2, 0.4])

        with c_ing:
            selected = st_searchbox(
                search_fn,
                key=f"ing_search_{k}",
                placeholder="Buscar ingrediente...",
                label="Ingrediente",
                label_visibility="collapsed",
            )

        # Si seleccionó "Crear X", crearlo y actualizar la selección
        if isinstance(selected, str) and selected.startswith(_NEW_PREFIX):
            name = selected[len(_NEW_PREFIX):]
            new_ing = ingredients_db.create(name)
            st.session_state[f"ing_search_{k}"] = (new_ing["name"], new_ing["id"])
            st.rerun()

        c_qty.number_input("Cant.", min_value=0.0, step=0.5, key=f"ing_qty_{k}", label_visibility="collapsed")
        c_unit.selectbox(
            "Unidad",
            options=unit_options,
            format_func=lambda x: "— unidad —" if x is None else unit_map.get(x, x),
            key=f"ing_unit_{k}",
            label_visibility="collapsed",
        )
        if c_rm.button("✕", key=f"ing_rm_{k}"):
            to_remove = k

    if to_remove is not None:
        st.session_state.f_ing_keys.remove(to_remove)
        st.rerun()

    if st.button("＋ Ingrediente"):
        k = st.session_state._f_ing_counter
        st.session_state.f_ing_keys.append(k)
        st.session_state._f_ing_counter += 1
        st.rerun()


# ── Sección de pasos ───────────────────────────────────────────

def _render_step_rows():
    to_remove = None
    for i, k in enumerate(st.session_state.f_step_keys):
        c_num, c_desc, c_rm = st.columns([0.3, 6, 0.4])
        c_num.markdown(f"**{i + 1}.**")
        c_desc.text_area("Paso", key=f"step_desc_{k}", label_visibility="collapsed", height=80)
        if c_rm.button("✕", key=f"step_rm_{k}"):
            to_remove = k

    if to_remove is not None:
        st.session_state.f_step_keys.remove(to_remove)
        st.rerun()

    if st.button("＋ Paso"):
        k = st.session_state._f_step_counter
        st.session_state.f_step_keys.append(k)
        st.session_state._f_step_counter += 1
        st.rerun()


# ── Guardado ───────────────────────────────────────────────────

def _save(recipe_id: str | None, ingredients: list):
    title = st.session_state.f_title.strip()
    if not title:
        st.error("El título es obligatorio.")
        return

    # El searchbox guarda el valor como tupla (label, id) o None
    def _get_ing_id(k):
        val = st.session_state.get(f"ing_search_{k}")
        if isinstance(val, tuple):
            return val[1]
        return val

    ingredient_rows = []
    for k in st.session_state.f_ing_keys:
        ing_id = _get_ing_id(k)
        if not ing_id or ing_id.startswith(_NEW_PREFIX):
            continue
        qty = st.session_state.get(f"ing_qty_{k}") or None
        unit_id = st.session_state.get(f"ing_unit_{k}")
        if qty and not unit_id:
            st.error(f"Falta la unidad para uno de los ingredientes.")
            return
        ingredient_rows.append({"ingredient_id": ing_id, "quantity": qty, "unit_id": unit_id})

    step_rows = [
        {"description": st.session_state.get(f"step_desc_{k}", "").strip()}
        for k in st.session_state.f_step_keys
        if st.session_state.get(f"step_desc_{k}", "").strip()
    ]

    data = {
        "title": title,
        "description": st.session_state.f_description.strip() or None,
        "cook_time": st.session_state.f_tiempo or None,
        "servings": st.session_state.f_servings or None,
        "ingredients": ingredient_rows,
        "steps": step_rows,
        "tag_ids": st.session_state.f_tag_ids,
    }

    if recipe_id:
        recipes_db.update(recipe_id, data)
        st.success("Receta actualizada.")
    else:
        recipe = recipes_db.create(data)
        st.session_state._f_loaded = None  # Resetea para que el próximo /create arranque vacío
        st.query_params["page"] = "recipe"
        st.query_params["id"] = recipe["id"]
        st.rerun()
