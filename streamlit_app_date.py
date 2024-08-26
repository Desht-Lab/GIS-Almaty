import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
import json
import geopandas as gpd
import datetime

# Load your data
merged_gdf = pd.read_pickle('retrospective.pkl')

# Extract year from registerDate
merged_gdf['registerDate'] = pd.to_datetime(merged_gdf['registerDate']).fillna( datetime.datetime.now())
merged_gdf['year'] = merged_gdf['registerDate'].dt.year

# Streamlit slider for selecting the year
min_year = int(merged_gdf['year'].min())
max_year = int(merged_gdf['year'].max())

selected_year = st.slider("Select Year", min_year, max_year, min_year)

# Filter data based on the selected year
filtered_gdf = merged_gdf[merged_gdf['year'] <= selected_year]

# Group by geometry and count the number of companies
grouped_df = filtered_gdf.groupby(['geometry']).size().reset_index(name='company_count')
grouped_df = gpd.GeoDataFrame(grouped_df, geometry='geometry')

# Convert grouped GeoDataFrame to GeoJSON format
geojson = json.loads(grouped_df.to_json())

# Define a Pydeck layer with elevation based on the count of companies
def get_fill_color(row):
    value = row['company_count']
    max_value = grouped_df['company_count'].max()
    min_value = grouped_df['company_count'].min()
    
    if max_value == min_value:
        # Avoid division by zero, return white color
        return [255, 255, 255]
    
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

layer = pdk.Layer(
    "GeoJsonLayer",
    data=geojson,
    get_fill_color="properties.fill_color",
    get_elevation="properties.company_count",
    elevation_scale=50,
    pickable=True,
    extruded=True,
)
view_state = pdk.ViewState(
    latitude=43.262482, 
    longitude=76.912051,
    zoom=9.1,
    pitch=160,  # Adjust the pitch to tilt the view
    bearing=0  # You can also adjust the bearing to rotate the view
)


# Create the deck.gl map
r = pdk.Deck(
    layers=[layer],
        initial_view_state=view_state,

    map_style='road',
    tooltip={"text": "{company_count}"},
)

# Display the map
st.pydeck_chart(r)
