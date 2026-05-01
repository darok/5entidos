from db.client import get_client

def get_all() -> list[dict]:
    client = get_client()
    res = client.table("ingredients").select("*").order("name").execute()
    return res.data

def create(name: str) -> dict:
    client = get_client()
    res = client.table("ingredients").insert({"name": name.strip()}).execute()
    return res.data[0]

def update(ingredient_id: str, name: str) -> dict:
    client = get_client()
    res = client.table("ingredients").update({"name": name.strip()}).eq("id", ingredient_id).execute()
    return res.data[0]

def delete(ingredient_id: str) -> None:
    client = get_client()
    client.table("ingredients").delete().eq("id", ingredient_id).execute()
