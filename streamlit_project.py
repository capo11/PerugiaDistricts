import streamlit as st
import geopandas as gpd
from shapely.geometry import Point
import requests
import folium
from streamlit_folium import st_folium

st.title("Perugia's Districts")

# --- Inizializza lo stato ---
for key in ["coords", "rione_trovato", "indirizzo_selezionato"]:
    if key not in st.session_state:
        st.session_state[key] = None

# carica rioni
rioni = gpd.read_file("rioni.json")
rioni = rioni[["name", "geometry"]]
rioni = rioni.set_crs("EPSG:4326")

# colori dei rioni
colori_rioni = {
    "Porta Sant'Angelo": "#d32f2f",
    "Porta Sole": "#ffffff",
    "Porta San Pietro": "#fbc02d",
    "Porta Eburnea": "#388e3c",
    "Porta Santa Susanna": "#1976d2"
}

indirizzo_input = st.text_input("Write an Address Perugia (without house number)", 
                                value=st.session_state.indirizzo_selezionato or "")

def geocode(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address + ", Perugia, Italy", "format": "json", "limit": 1}
    headers = {"User-Agent": "streamlit-rioni"}
    r = requests.get(url, params=params, headers=headers)
    data = r.json()
    if len(data) == 0:
        return None
    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])
    return lat, lon

# --- Bottone Trova rione ---
if st.button("Find district") and indirizzo_input.strip() != "":
    coords = geocode(indirizzo_input)
    if coords:
        st.session_state.coords = coords
        st.session_state.indirizzo_selezionato = indirizzo_input
        lat, lon = coords
        punto = Point(lon, lat)
        match = rioni[rioni.contains(punto)]
        if not match.empty:
            st.session_state.rione_trovato = match.iloc[0]["name"]
        else:
            st.session_state.rione_trovato = None
            st.warning("Address outside the districts")
    else:
        st.error("Address not found")

# --- Leggi stato corrente ---
coords = st.session_state.coords
rione_trovato = st.session_state.rione_trovato
indirizzo_selezionato = st.session_state.indirizzo_selezionato

# Mostra il rione trovato
if rione_trovato:
    st.success(f"The district is: {rione_trovato}")

# --- Crea mappa ---
mappa = folium.Map(location=[43.11, 12.39], zoom_start=12)

def style_function(feature):
    nome = feature["properties"]["name"]
    colore = colori_rioni.get(nome, "#3388ff")
    if rione_trovato == nome:
        return {"fillColor": colore, "color": "black", "weight": 4, "fillOpacity": 0.7}
    return {"fillColor": colore, "color": "black", "weight": 1, "fillOpacity": 0.3}

# aggiungi rioni
folium.GeoJson(
    rioni.to_json(),
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["District:"])
).add_to(mappa)

# aggiungi marker indirizzo
if coords:
    lat, lon = coords
    folium.Marker(
        location=[lat, lon],
        popup=indirizzo_selezionato,
        tooltip="Indirizzo selezionato",
        icon=folium.Icon(color="red", icon="home")
    ).add_to(mappa)
    mappa.location = [lat, lon]
    mappa.zoom_start = 15

# mostra mappa
st_folium(mappa, width=700, height=500)