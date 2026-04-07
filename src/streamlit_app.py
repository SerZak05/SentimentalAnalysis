import streamlit as st
import folium
from streamlit_folium import st_folium
from collections import defaultdict
# from joblib import Parallel, delayed
from post_assesment import get_sentiment, emotions
from post_search import search_posts_parallel

emotion_to_color = {
    'no_emotion': "#666666",
    'joy': "#33cc33",
    'sadness': "#0066ff",
    'surprise': "#ff9900",
    'fear': "#aa2fd6",
    'anger': "#ff0000"
}

POSTS_CNT = 500
# TOP_CITIES_CNT = 2
NUM_OF_WORKERS = 8
# top_cities = cities_db.nlargest(n=TOP_CITIES_CNT, columns="population")

# === Beginning of the page ===
st.title("Sentiment analysis")
topic = st.text_input("Enter your topic:", "котики")
button = st.button("Start!")

if button:
    st.session_state["running"] = True
    st.session_state.pop("results", None)
    st.session_state.pop("posts", None)

if st.session_state.get("running", False):
    st.text("Processing query...")
    st.session_state["posts"] = search_posts_parallel(topic, POSTS_CNT)
    # posts_per_city = Parallel(n_jobs=NUM_OF_WORKERS) \
    # (
    #     delayed(search_posts_by_pos)(topic, POSTS_CNT, city_row["city"], city_row["lat"], city_row["lon"]) 
    #     for ind, city_row in top_cities.iterrows()
    # )
    # posts = [post for city_list in posts_per_city for post in city_list]
    # print(*[post.owner_id for post in posts], sep='\n', flush=True)
    # st.session_state["posts"] = posts
    st.text("Gathered posts...")
    st.session_state["results"] = get_sentiment(st.session_state["posts"])
    # st.write(st.session_state["results"])
    st.session_state["running"] = False
    
if "results" in st.session_state:
    print("Got results!", flush=True)
    posts = st.session_state["posts"]
    results = st.session_state["results"]
    scores = defaultdict(lambda: {e: 0.0 for e in emotions})
    cnt = defaultdict(int)
    names = {}
    for i in range(len(posts)):
        pos = posts[i].geolocation
        names[pos] = posts[i].city_of_origin
        cnt[pos] += 1
        # for label, score in results[i].items():
        #     scores[pos][label] = score
        scores[pos][results[i]["label"]] = results[i]["score"] if results[i]["label"] != "no_emotion" else 0.001
    colors = {pos: emotion_to_color[max(score, key=score.get)] for pos, score in scores.items()}
    map_table = {
        "lon": [pos[0] for pos in cnt.keys()],
        "lat": [pos[1] for pos in cnt.keys()],
        "color": colors,
        "size": cnt.values()
    }
    m = folium.Map()
    for pos in cnt.keys():
        # print(pos)
        folium.CircleMarker((float(pos[0]), float(pos[1])), radius=cnt[pos] / POSTS_CNT * 100, color=colors[pos]).add_to(m)
    st_folium(m, width=725, returned_objects=[])
    # st.map(map_table, latitude="lat", longitude="lon", color="color", size="size")