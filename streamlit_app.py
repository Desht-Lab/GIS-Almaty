import streamlit as st
import pydeck as pdk
import geopandas as gpd
import pandas as pd
import h3
from shapely.geometry import Polygon
import numpy as np

# Load your data
fields = pd.read_excel('группировка отраслей.xlsx')
almaty_XY = pd.read_pickle('finalAlmatyFixedForCityClustering.pkl')
almatyAglo_XY = pd.read_pickle('finalAgloNewCleanWhole-Sana.pkl')
almaty_XY = pd.concat([almatyAglo_XY, almaty_XY])

fields['oked5'] = fields['oked5'].astype(str).str.zfill(5)
almaty_XY = almaty_XY.merge(fields[['oked5', 'Fields', 'Desc']], left_on="oked",
                            right_on="oked5", how='left', validate="m:1")

full_df = almaty_XY[~almaty_XY['x'].isna()]
full_df = gpd.GeoDataFrame(
    full_df, geometry=gpd.points_from_xy(full_df.x, full_df.y))

# One-hot encode the 'Desc' column
df_one_hot = pd.get_dummies(full_df, columns=['Desc'])

# Replace the 1s in the one-hot encoded columns with the corresponding 'emp' values
for col in df_one_hot.columns:
    if (col.startswith('Desc_')):
        section = col.split('_')[-1]
        df_one_hot[col] = df_one_hot[col] * full_df['emp']

# Drop the original 'emp' column
df_one_hot = df_one_hot.drop(columns=['emp'])

# Aggregate by 'x' and 'y' columns
columns_to_sum = [col for col in df_one_hot.columns if col.startswith('Desc_')]
df_aggregated = df_one_hot.groupby(['x', 'y'])[columns_to_sum].sum().reset_index()

def h3_hexagon_polygon(hex_id):
    """Convert H3 hex id to a Shapely polygon."""
    boundary = h3.h3_to_geo_boundary(hex_id, geo_json=True)
    return Polygon(boundary)

# Step 1: Choose an appropriate resolution
resolution = 9

# Step 2: Convert points to H3 indices
df_aggregated['h3_index'] = df_aggregated.apply(lambda row: h3.geo_to_h3(float(row.y), float(row.x), resolution), axis=1)

# Step 3: Aggregate data based on H3 indices
hexagon_gdf = df_aggregated.groupby('h3_index')[columns_to_sum].sum().reset_index()

# Step 4: Convert H3 indices to hexagon polygons
hexagon_gdf['geometry'] = hexagon_gdf['h3_index'].apply(h3_hexagon_polygon)

# Convert to GeoDataFrame
hexagon_gdf = gpd.GeoDataFrame(hexagon_gdf, geometry='geometry')

# Simplify column names
hexagon_gdf.columns = [
    col.split('_')[1] if '_' in col else col
    for col in hexagon_gdf.columns
]
modified_column_names = [col.split('_')[1] for col in columns_to_sum]
hexagon_gdf['Все'] = hexagon_gdf[modified_column_names].sum(axis = 1)
modified_column_names.insert(0, 'Все')

# Streamlit UI
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
    elevation_scale=500 if log_scale else 5,  # Elevation scale based on log scale
    extruded=use_elevation,
    pickable=True,
    auto_highlight=True,
)

# Initial view settings based on the centroid of your map
view_state = pdk.ViewState(
    latitude=43.536224,
    longitude=76.938093,
    zoom=8,
    pitch=45 if use_elevation else 0,
)

# Render the map
deck = pdk.Deck(
    map_style='mapbox://styles/mapbox/streets-v12',
    initial_view_state=view_state,
    layers=[layer],
)

# Display in Streamlit
st.pydeck_chart(deck)