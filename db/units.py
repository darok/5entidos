from db.client import get_client

def get_all() -> list[dict]:
    client = get_client()
    res = client.table("units").select("*").order("name").execute()
    return res.data

def create(name: str, abbreviation: str) -> dict:
    client = get_client()
    res = client.table("units").insert({"name": name.strip(), "abbreviation": abbreviation.strip()}).execute()
    return res.data[0]

def update(unit_id: str, name: str, abbreviation: str) -> dict:
    client = get_client()
    res = client.table("units").update({"name": name.strip(), "abbreviation": abbreviation.strip()}).eq("id", unit_id).execute()
    return res.data[0]

def delete(unit_id: str) -> None:
    client = get_client()
    client.table("units").delete().eq("id", unit_id).execute()
