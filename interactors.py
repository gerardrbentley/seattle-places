from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Tuple

import httpx
import toml

creds = toml.load(".streamlit/secrets.toml")
pocketbase_url = creds.get("pocketbase_url")
pocketbase_username = creds.get("pocketbase_username")
pocketbase_password = creds.get("pocketbase_password")
google_place_api_key = creds.get("google_places_api_key")


@dataclass
class Place:
    record_id: str
    name: str
    description: str
    category: str
    tags: str
    cost_per_person: int
    homepage: str
    maps_url: str
    lat: float
    lon: float
    rating: float


@lru_cache(1)
def get_token() -> str:
    response = httpx.post(
        f"{pocketbase_url}/api/collections/users/auth-with-password",
        json={
            "identity": pocketbase_username,
            "password": pocketbase_password,
        },
    )
    try:
        response.raise_for_status()
        auth_data = response.json()
        token = auth_data.get("token")
    except Exception as e:
        print(repr(e))
        return ""
    return token


def get_mappings(table_name):
    token = get_token()
    if token == "":
        print("Unable to get token")
        return None

    response = httpx.get(
        f"{pocketbase_url}/api/collections/{table_name}/records",
        headers={"Authorization": token},
    )
    response.raise_for_status()
    data = response.json()["items"]
    return {x["name"]: x["id"] for x in data}


def update_place(record, record_id):
    token = get_token()
    if token == "":
        print("Unable to get token")
        return None

    response = httpx.patch(
        f"{pocketbase_url}/api/collections/places/records/{record_id}",
        headers={"Authorization": token},
        json=record,
    )
    return response


def add_place(record):
    token = get_token()
    if token == "":
        print("Unable to get token")
        return None

    response = httpx.post(
        f"{pocketbase_url}/api/collections/places/records",
        headers={"Authorization": token},
        json=record,
    )
    return response


def get_data() -> Tuple[Dict[str, Place], Dict[str, str], Dict[str, str]]:
    token = get_token()
    if token == "":
        print("Unable to get token")
        return {}, {}, {}

    response = httpx.get(
        f"{pocketbase_url}/api/collections/places/records",
        headers={"Authorization": token},
        params={
            "perPage": 300,
            "sort": "name",
            "expand": ",".join(("category", "tags")),
        },
    )
    try:
        response.raise_for_status()
        raw_data = response.json()
        data = [parse_place(record) for record in raw_data["items"]]
        mapping = {x.name: x for x in data}
    except Exception as e:
        print(repr(e))
        return {}, {}, {}
    try:
        categories = get_mappings("categories")
    except Exception as e:
        print(repr(e))
        return {}, {}, {}
    try:
        tags = get_mappings("tags")
    except Exception as e:
        print(repr(e))
        return {}, {}, {}

    return mapping, categories, tags


def parse_place(raw: dict) -> Place:
    place = Place(
        record_id=raw.get("id", "Unknown"),
        name=raw.get("name", "Unknown"),
        cost_per_person=raw.get("cost_per_person", 0),
        homepage=raw.get("homepage", "Unknown"),
        maps_url=raw.get("maps_url", "Unknown"),
        lat=raw.get("lat", 0),
        lon=raw.get("lon", 0),
        description=raw.get("description", "Unknown"),
        category="Unknown",
        tags="",
        rating=raw.get("rating", 0),
    )

    joined_data = raw.get("expand")
    if joined_data is not None:
        category = joined_data.get("category")
        if category is not None:
            place.category = category.get("name", "Unknown")

        tags = joined_data.get("tags")
        if tags is not None:
            tag_names = {tag.get("name", "Unknown") for tag in tags}
            place.tags = ",".join(tag_names)

    return place


def lookup_place(name: str):
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"

    response = httpx.get(
        url,
        params={
            "input": name,
            "inputtype": "textquery",
            "locationbias": "circle:10000@47.6074883,-122.3293073",
            "fields": "place_id",
            # "fields": "name,rating,geometry,url",
            "key": google_place_api_key,
        },
    )

    response.raise_for_status()
    print(response.request.url)
    candidates = response.json().get("candidates")
    if candidates is None:
        raise Exception("Place Not Found")
    place_id = candidates[0].get("place_id")
    url = "https://maps.googleapis.com/maps/api/place/details/json"

    response = httpx.get(
        url,
        params={
            "place_id": place_id,
            # "fields": "name,rating,geometry,url",
            "key": google_place_api_key,
        },
    )

    response.raise_for_status()
    return response.json()
