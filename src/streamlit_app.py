import streamlit as st
import folium
from streamlit_folium import st_folium
from collections import defaultdict
import heapq
from post_assesment import get_sentiment, emotions
from post_search import search_posts

emotion_to_color = {
    'no_emotion': "#666666",
    'joy': "#33cc33",
    'sadness': "#0066ff",
    'surprise': "#ff9900",
    'fear': "#aa2fd6",
    'anger': "#ff0000"
}

# POSTS_CNT = 500
# TOP_CITIES_CNT = 2
NUM_OF_WORKERS = 8
# top_cities = cities_db.nlargest(n=TOP_CITIES_CNT, columns="population")

# === Beginning of the page ===
st.set_page_config("Sentiment analysis", layout="wide")
st.title("Sentiment analysis")
topic = st.text_input("Enter your topic:", "котики")
posts_cnt = st.slider("Number of posts to gather:", 10, 500, 10, step=10)
button = st.button("Start!")

if button:
    st.session_state["running"] = True
    st.session_state.pop("results", None)
    st.session_state.pop("posts", None)
    st.session_state["posts_cnt"] = posts_cnt

if st.session_state.get("running", False):
    st.text("Gathering posts...")
    st.session_state["posts"] = search_posts(topic, st.session_state["posts_cnt"])
    st.text("Evaluating sentiment...")
    st.session_state["results"] = get_sentiment(st.session_state["posts"])
    st.text("Done!")
    st.session_state["running"] = False
    
if "results" in st.session_state:
    posts = st.session_state["posts"]
    results = st.session_state["results"]
    scores = defaultdict(lambda: {e: 0.0 for e in emotions})
    cnt = defaultdict(int)
    names = {}
    for i in range(len(posts)):
        pos = posts[i].geolocation
        names[pos] = posts[i].city_of_origin
        cnt[pos] += 1
        scores[pos][results[i]["label"]] += results[i]["score"] if results[i]["label"] != "no_emotion" else 0.001

    colors = {pos: emotion_to_color[max(score, key=score.get)] for pos, score in scores.items()}
    emo = {pos: max(score, key=score.get) for pos, score in scores.items()}
    
    example_texts = {}
    selected_posts = defaultdict(list)
    for i, post in enumerate(posts):
        if results[i]["label"] == emo[post.geolocation]:
            selected_posts[post.geolocation].append((post, results[i]["score"]))

    for pos in cnt.keys():
        example_texts[pos] = heapq.nlargest(5, selected_posts[pos], key=lambda p: p[1])


    col1, col2 = st.columns(2)
    with col1:
        m = folium.Map()
        for pos in cnt.keys():
            folium.CircleMarker(
                (float(pos[0]), float(pos[1])), 
                radius=cnt[pos] / st.session_state["posts_cnt"] * 100, 
                color=colors[pos],
                fill=True,
                fill_opacity=0.5,
                tooltip=f"{emo[pos]}: {scores[pos][emo[pos]]}",
                popup=f"# of posts: {cnt[pos]}"
            ).add_to(m)
    
    
        folium_output = st_folium(m, width=800, returned_objects=["last_object_clicked"])

    with col2:
        # Displaying examples
        if folium_output["last_object_clicked"] is not None:
            obj = folium_output["last_object_clicked"]
            clicked_pos = (obj["lat"], obj["lng"])
            all_pos = cnt.keys()
            closest_pos = min(all_pos, key=lambda p: abs(p[0] - clicked_pos[0]) + abs(p[1] - clicked_pos[1]))
            for p in example_texts[closest_pos]:
                st.markdown(f"###### Post (score = {p[1]}):")
                st.text(p[0].text)