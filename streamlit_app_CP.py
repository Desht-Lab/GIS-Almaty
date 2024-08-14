import streamlit as st
import pydeck as pdk
import geopandas as gpd
import pandas as pd
import h3
from shapely.geometry import Polygon
import numpy as np
import json

# Load your data

almaty_XY = pd.read_pickle('CP_Hex_res9.pkl')


full_df = gpd.GeoDataFrame(almaty_XY)

# Define the URL you want to redirect to
url = "https://desht-lab.github.io/GIS-Almaty/"


st.markdown(f'<a href="{url}" style="display:inline-block; padding:5px 10px; font-size:16px; color:#fff; background-color:#0e1117; border: 2px solid #ffffff; border-radius:5px; text-decoration:none;">Назад</a>', 
            unsafe_allow_html=True)
st.title("Модель центр-периферия")


# Toggle elevation
use_elevation = st.checkbox("Добавить высоту", value=False)

remove_zeros = st.checkbox("Убрать не значимые гексагоны", value=False)

opacity  = st.number_input(
    "Введите прозрачность слоя", value=0.3, placeholder="Введите число", min_value = 0.1, max_value = 1.0
)

# Filter out hexagons with zero values if the checkbox is selected
if remove_zeros:
    hexagon_gdf = full_df[full_df['Significant'] == True]
else:
    hexagon_gdf = full_df.copy()

geojson = json.loads(hexagon_gdf[['geometry', 'emp', 'color_rgba', 'top_5_companies']].to_json())





# Configure Pydeck Layer
layer = pdk.Layer(
    'GeoJsonLayer',
    geojson,
    get_fill_color='properties.color_rgba',  # Use the calculated fill color
    get_elevation=f"properties.emp",  # Elevation based on selected filter
    opacity=opacity,
    stroked=False,  # Disable contours
    filled=True,
    wireframe=False,  # Disable wireframe
    elevation_scale=2,  # Elevation scale based on log scale
    extruded=use_elevation,
    pickable=True,
    auto_highlight=True,
)

# Initial view settings based on the centroid of your map
view_state = pdk.ViewState(
    latitude=43.262482, 
    longitude=76.912051,
    zoom=9,
    pitch=45 if use_elevation else 0,
)

# Render the map
deck = pdk.Deck(
    map_style='mapbox://styles/mapbox/streets-v12',
    initial_view_state=view_state,
    layers=[layer],
    tooltip = {
    "html": "<b>{emp}</b> условная занятость на локации<br> <b>Топ 5 компаний:</b> {top_5_companies}",
    "style": {"background": "grey", "color": "white", "font-family": '"Helvetica Neue", Arial', "z-index": "10000"},
}
)

# Display in Streamlit
st.pydeck_chart(deck)