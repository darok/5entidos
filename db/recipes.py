from db.client import get_client


def get_all() -> list[dict]:
    client = get_client()
    res = client.table("recipes").select(
        "*, recipe_tags(tag_id, tags(id, name))"
    ).order("created_at", desc=True).execute()
    return res.data


def get_by_id(recipe_id: str) -> dict | None:
    client = get_client()
    recipe = client.table("recipes").select("*").eq("id", recipe_id).single().execute().data
    if not recipe:
        return None
    recipe["ingredients"] = client.table("recipe_ingredients").select(
        "*, ingredients(name), units(name, abbreviation)"
    ).eq("recipe_id", recipe_id).execute().data
    recipe["steps"] = client.table("recipe_steps").select("*").eq(
        "recipe_id", recipe_id
    ).order("step_number").execute().data
    recipe["tags"] = client.table("recipe_tags").select(
        "tag_id, tags(id, name, tag_types(name))"
    ).eq("recipe_id", recipe_id).execute().data
    return recipe


def create(data: dict) -> dict:
    client = get_client()
    recipe = client.table("recipes").insert(_recipe_fields(data)).execute().data[0]
    _save_related(client, recipe["id"], data)
    return recipe


def update(recipe_id: str, data: dict) -> dict:
    client = get_client()
    recipe = client.table("recipes").update(_recipe_fields(data)).eq("id", recipe_id).execute().data[0]
    client.table("recipe_ingredients").delete().eq("recipe_id", recipe_id).execute()
    client.table("recipe_steps").delete().eq("recipe_id", recipe_id).execute()
    client.table("recipe_tags").delete().eq("recipe_id", recipe_id).execute()
    _save_related(client, recipe_id, data)
    return recipe


def delete(recipe_id: str) -> None:
    client = get_client()
    client.table("recipes").delete().eq("id", recipe_id).execute()


# ── helpers ──────────────────────────────────────────────────

def _recipe_fields(data: dict) -> dict:
    keys = ("title", "description", "prep_time", "cook_time", "servings")
    return {k: data[k] for k in keys if k in data}


def _save_related(client, recipe_id: str, data: dict) -> None:
    _save_ingredients(client, recipe_id, data.get("ingredients", []))
    _save_steps(client, recipe_id, data.get("steps", []))
    _save_tags(client, recipe_id, data.get("tag_ids", []))


def _save_ingredients(client, recipe_id: str, ingredients: list[dict]) -> None:
    rows = [
        {
            "recipe_id": recipe_id,
            "ingredient_id": ing["ingredient_id"],
            "quantity": ing.get("quantity"),
            "unit_id": ing.get("unit_id"),
        }
        for ing in ingredients if ing.get("ingredient_id")
    ]
    if rows:
        client.table("recipe_ingredients").insert(rows).execute()


def _save_steps(client, recipe_id: str, steps: list[dict]) -> None:
    rows = [
        {"recipe_id": recipe_id, "step_number": i + 1, "description": step["description"]}
        for i, step in enumerate(steps) if step.get("description", "").strip()
    ]
    if rows:
        client.table("recipe_steps").insert(rows).execute()


def _save_tags(client, recipe_id: str, tag_ids: list[str]) -> None:
    if tag_ids:
        rows = [{"recipe_id": recipe_id, "tag_id": tid} for tid in tag_ids]
        client.table("recipe_tags").insert(rows).execute()
