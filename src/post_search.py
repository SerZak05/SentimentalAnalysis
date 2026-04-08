import vk_api
from dotenv import load_dotenv
import os
from dataclasses import dataclass
import numpy as np
import streamlit as st
import pandas as pd

load_dotenv()

@st.cache_resource
def connect_api():
    service_token = os.getenv("VK_TOKEN")
    return vk_api.VkApi(token=service_token).get_api()

vk = connect_api()

@st.cache_resource
def get_cities_db():
    return pd.read_csv("towns.csv")

cities_db = get_cities_db()


@dataclass
class Post:
    text: str
    city_of_origin: str
    geolocation: tuple[float, float]
    # likes: int
    owner_id: int
    # group_owned: bool = False

def search_posts(query: str, num_of_posts: int, *, search_args = {}):
    posts: list[Post] = []
    request_count = 200
    start_from: str | None = None
    while len(posts) < num_of_posts:
        search_res, start_from = _get_posts(query, request_count, start_from, search_args)
        posts.extend(search_res)
        print(f"Added {len(posts)}, start_from={start_from}.", flush=True)
        if start_from is None:
            break
    return posts[:num_of_posts]


def _get_posts(query: str, request_count: int, start_from: str | None, search_args) -> tuple[list[Post], str | None]:
    posts = []
    if start_from is None:
        query_results = vk.newsfeed.search(q=query, count=request_count, **search_args)
    else:
        query_results = vk.newsfeed.search(q=query, count=request_count, start_from=start_from, **search_args)
    items = [item for item in query_results["items"] if "owner_id" in item and "text" in item]
    item_dict = {item["owner_id"]: item for item in items}
    owner_ids = np.array([item["owner_id"] for item in items])
    cities = get_post_city(owner_ids)
    city_pos = get_city_position(cities)
    # likes = item.get("likes", {"count": 0})["count"]
    for id, pos in city_pos.items():
        if pos is None:
            continue
        posts.append(Post(item_dict[id]["text"], cities[id], pos, id))
    assert all(post.geolocation is not None for post in posts)
    return posts, query_results.get("next_from", None)


def get_post_city(owner_id: np.ndarray) -> dict[int, str | None]:
    group_ids = -owner_id[owner_id < 0]
    user_ids = owner_id[owner_id > 0]
    assert len(group_ids) + len(user_ids) == len(owner_id)
    # print(group_ids, user_ids, owner_id, flush=True)
    if len(group_ids) > 0:
        groups = vk.groups.getById(group_ids=list(group_ids), fields=['city', 'country'])
        groups_dict = {-group["id"]: group.get("city", None) for group in groups}
    else:
        groups_dict = {}
    if len(user_ids) > 0:
        users = vk.users.get(user_ids=list(user_ids), fields=['city', 'country'])
        users_dict = {user["id"]: user.get("city", None) for user in users}
    else:
        users_dict = {}
    
    users_dict.update(groups_dict)
    return {id: city["title"] if city is not None else None for id, city in users_dict.items()}
    

def get_city_position(cities: dict[int, str | None]) -> dict[int, tuple[float, float] | None]:
    res = {}
    for id, city in cities.items():
        if city is None:
            res[id] = None
            continue
        selected = cities_db[cities_db["city"] == city]
        if len(selected) == 0:
            res[id] = None
            continue
        # print(selected)
        res[id] = (selected["lat"].iloc[0], selected["lon"].iloc[0])
    assert len(cities) == len(res)
    return res


def search_posts_by_pos(query: str, num_of_posts: int, city_name: str, lat: float, lon: float) -> list[Post]:
    posts: list[Post] = []
    offset = 0
    request_count = min(num_of_posts, 200)
    while len(posts) < num_of_posts:
        query_results = vk.newsfeed.search(q=query, count=request_count, offset=offset, latitude=lat, longtitude=lon)
        items = [item for item in query_results["items"] if "text" in item]
        for item in items:
            posts.append(Post(item["text"], city_name, (lat, lon), item.get("owner_id", 0)))
        offset += request_count
        print(f"For city {city_name} processed {offset} posts, added {len(posts)}.", flush=True)
    return posts[:num_of_posts]