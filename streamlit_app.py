import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np


hexagon_gdf = pd.read_pickle('descriptive_data_app.pkl')
# Load your data
fields = pd.read_excel('группировка отраслей.xlsx')

fields_sorted = fields.sort_values(by=['grand_section_code', 'oked2']).dropna()
modified_column_names = fields_sorted['Desc'].unique().tolist()
modified_column_names.insert(0, 'Все')


st.title("Описательная статистика Алматинской агломерации")

# Filter selection
selected_filter = st.selectbox("Выбрать отрасль", modified_column_names)

# Toggle between logarithmic and absolute scale (default is logarithmic)
log_scale = st.checkbox("Логарифмическая шкала", value=True)

# Toggle elevation
use_elevation = st.checkbox("Добавить высоту", value=False)

remove_zeros = st.checkbox("Убрать нулевую занятость", value=False)


# Filter out hexagons with zero values if the checkbox is selected
if remove_zeros:
    hexagon_gdf = hexagon_gdf[hexagon_gdf[selected_filter] > 0]

# Apply logarithmic scale if selected
hexagon_gdf['empl'] = hexagon_gdf[selected_filter]
if log_scale:
    hexagon_gdf[selected_filter] = np.log1p(hexagon_gdf[selected_filter])



# Manually create GeoJSON for Pydeck
features = []
for _, row in hexagon_gdf.iterrows():
    feature = {
        "type": "Feature",
        "geometry": row["geometry"].__geo_interface__,
        "properties": {col: row[col] for col in modified_column_names},
    }
    feature["properties"]["top_5_companies"] = row["top_5_companies"]
    feature["properties"]["empl"] = row["empl"]
    features.append(feature)

geojson = {
    "type": "FeatureCollection",
    "features": features,
}

def get_fill_color(row):
    value = row[selected_filter]
    max_value = hexagon_gdf[selected_filter].max()
    min_value = hexagon_gdf[selected_filter].min()
    
    # Calculate ratio
    ratio = (value - min_value) / (max_value - min_value)
    
    if ratio < 0.5:
        # Blue to White scale
        return [
            int(0), 
            int(2 * 255 * ratio), 
            int(255)  # Blue to White
        ]
    else:
        # White to Red scale
        return [
            int(2 * 255 * (ratio - 0.5)), 
            int(255 * (1 - 2 * (ratio - 0.5))), 
            int(255 * (1 - 2 * (ratio - 0.5)))  # White to Red
        ]

# Add fill color to properties
for feature in geojson["features"]:
    feature["properties"]["fill_color"] = get_fill_color(feature["properties"])

# Configure Pydeck Layer
layer = pdk.Layer(
    'GeoJsonLayer',
    geojson,
    get_fill_color='properties.fill_color',  # Use the calculated fill color
    get_elevation=f"properties['{selected_filter}']",  # Elevation based on selected filter
    opacity=0.2,
    stroked=False,  # Disable contours
    filled=True,
    wireframe=False,  # Disable wireframe
    elevation_scale=500 if log_scale else 2,  # Elevation scale based on log scale
    extruded=use_elevation,
    pickable=True,
    auto_highlight=True,
)

# Initial view settings based on the centroid of your map
view_state = pdk.ViewState(
    latitude=43.262482, 
    longitude=76.912051,
    zoom=9,
    pitch=45 if use_elevation else 0
)

# Render the map
deck = pdk.Deck(
    map_style='mapbox://styles/mapbox/streets-v12',
    initial_view_state=view_state,
    layers=[layer],
    tooltip = {
    "html": "<b>{empl}</b> условная занятость на локации<br> <b>Топ 5 компаний:</b> {top_5_companies}",
    "style": {"background": "grey", "color": "white", "font-family": '"Helvetica Neue", Arial', "z-index": "10000"},
} if selected_filter == 'Все' else {
    "html": "<b>{empl}</b> условная занятость на локации",
    "style": {"background": "grey", "color": "white", "font-family": '"Helvetica Neue", Arial', "z-index": "10000"},
}
)

# Display in Streamlit
st.pydeck_chart(deck)