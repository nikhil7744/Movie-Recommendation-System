import pickle
import streamlit as st
import requests
import pandas as pd


import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ─── Configure a Session with Retries ─────────────────────────────
session = requests.Session()
retry_strategy = Retry(
    total=5,                 # up to 5 retries on failure
    backoff_factor=1,        # waits 1s, then 2s, then 4s…
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

# ─── Poster Fetch Function ────────────────────────────────────────
def fetch_poster(movie_id):
    """
    Fetches the poster URL for a given TMDb movie_id.
    Returns a valid poster URL or a placeholder if unavailable.
    """
    url = (
        f"https://api.themoviedb.org/3/movie/{movie_id}"
        f"?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
    )
    try:
        resp = session.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        path = data.get("poster_path")
        if path:
            return f"https://image.tmdb.org/t/p/w500{path}"
    except requests.exceptions.RequestException:
        pass

    # Fallback placeholder with text
    return "https://via.placeholder.com/500x750?text=Poster+currently+not+available"


def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []
    for i in distances[1:6]:
        # fetch the movie poster
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movie_posters.append(fetch_poster(movie_id))
        recommended_movie_names.append(movies.iloc[i[0]].title)

    return recommended_movie_names,recommended_movie_posters


st.header('🎬 Movie Recommender System')
# movies = pickle.load(open('model/movie_list.pkl','rb'))
# similarity = pickle.load(open('model/similarity.pkl','rb'))

movie_dict = pickle.load(open("movie_dict.pkl", "rb"))
movies = pd.DataFrame(movie_dict)
similarity = pickle.load(open("similarity.pkl", "rb"))



movie_list = movies['title'].values
selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movie_list
)

if st.button('Show Recommendation'):
    recommended_movie_names,recommended_movie_posters = recommend(selected_movie)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.text(recommended_movie_names[0])
        st.image(recommended_movie_posters[0])
    with col2:
        st.text(recommended_movie_names[1])
        st.image(recommended_movie_posters[1])

    with col3:
        st.text(recommended_movie_names[2])
        st.image(recommended_movie_posters[2])
    with col4:
        st.text(recommended_movie_names[3])
        st.image(recommended_movie_posters[3])
    with col5:
        st.text(recommended_movie_names[4])
        st.image(recommended_movie_posters[4])

def recommend(movie):
    import time

    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

    recommended_movie_names = []
    recommended_movie_posters = []

    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].movie_id
        poster_url = fetch_poster(movie_id)
        recommended_movie_posters.append(poster_url)
        recommended_movie_names.append(movies.iloc[i[0]].title)
        time.sleep(1)  # 1 second delay per request

    return recommended_movie_names, recommended_movie_posters
# ─── Poster Cache ─────────────────────────────
poster_cache = {}

# ─── Recommend Function with Auto‑Clear Cache ─────────────────────────────
def recommend(movie):
    # Clear the in‑memory cache on each call
    poster_cache.clear()

    index = movies[movies['title'] == movie].index[0]
    distances = sorted(
        list(enumerate(similarity[index])),
        reverse=True,
        key=lambda x: x[1]
    )

    movie_ids = [movies.iloc[i[0]].movie_id for i in distances[1:6]]
    recommended_movie_names = [movies.iloc[i[0]].title for i in distances[1:6]]

    # Parallel fetch posters
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_poster, m_id) for m_id in movie_ids]
        recommended_movie_posters = [f.result() for f in futures]

    return recommended_movie_names, recommended_movie_posters


