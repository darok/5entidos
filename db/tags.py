from db.client import get_client

def get_all_types() -> list[dict]:
    client = get_client()
    res = client.table("tag_types").select("*").order("name").execute()
    return res.data

def get_all() -> list[dict]:
    client = get_client()
    res = client.table("tags").select("*, tag_types(name)").order("name").execute()
    return res.data

def create_type(name: str) -> dict:
    client = get_client()
    res = client.table("tag_types").insert({"name": name.strip()}).execute()
    return res.data[0]

def create(name: str, tag_type_id: str | None = None) -> dict:
    client = get_client()
    res = client.table("tags").insert({"name": name.strip(), "tag_type_id": tag_type_id}).execute()
    return res.data[0]

def update_type(type_id: str, name: str) -> dict:
    client = get_client()
    res = client.table("tag_types").update({"name": name.strip()}).eq("id", type_id).execute()
    return res.data[0]

def delete_type(type_id: str) -> None:
    client = get_client()
    client.table("tag_types").delete().eq("id", type_id).execute()

def update_tag(tag_id: str, name: str, tag_type_id: str | None = None) -> dict:
    client = get_client()
    res = client.table("tags").update({"name": name.strip(), "tag_type_id": tag_type_id}).eq("id", tag_id).execute()
    return res.data[0]

def delete_tag(tag_id: str) -> None:
    client = get_client()
    client.table("tags").delete().eq("id", tag_id).execute()
