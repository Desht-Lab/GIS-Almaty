import streamlit as st
import pydeck as pdk
import geopandas as gpd
import pandas as pd
import h3
from shapely.geometry import Polygon
import numpy as np


# Load your data
fields = pd.read_excel('группировка отраслей.xlsx')
fields_sorted = fields.sort_values(by=['grand_section_code', 'oked2']).dropna()
modified_column_names = fields_sorted['Desc'].unique().tolist()
modified_column_names.insert(0, 'Все')
keys = pd.read_excel(r"C:\Users\temp.Sana.000\OneDrive\Desht\Digital lab\Предприятия\Scripts that download data from stat gov\keys entity.xlsx",
                     sheet_name = 'kopf')
keys = keys[keys['kopf'] != 741926]

# Filter selection
industry_filter = st.selectbox("Выбрать отрасль", modified_column_names)


# Toggle elevation
use_elevation = st.checkbox("Добавить высоту", value=False)

almaty_XY = pd.read_pickle('finalAlmatyFixedForCityClustering.pkl')
almatyAglo_XY = pd.read_pickle('finalAgloNewCleanWhole-Sana.pkl')
almaty_XY = pd.concat([almatyAglo_XY, almaty_XY])

fields['oked5'] = fields['oked5'].astype(str).str.zfill(5)
almaty_XY = almaty_XY.merge(fields[['oked5', 'Fields', 'Desc']], left_on="oked",
                            right_on="oked5", how='left', validate="m:1")

full_df = almaty_XY[~almaty_XY['x'].isna()]
full_df = gpd.GeoDataFrame(
    full_df, geometry=gpd.points_from_xy(full_df.x, full_df.y))

full_df = full_df.merge(keys[['kopf', 'Наименование на русском языке']], 
                        how = 'left', validate = 'm:1')
kopf = list(full_df['Наименование на русском языке'].unique())
kopf.insert(0, 'Все')
kopf_filter = st.selectbox("Выбрать отрасль", kopf)
if industry_filter != 'Все':
    full_df = full_df[full_df['Desc'] == industry_filter].reset_index(drop=True)
if kopf_filter != 'Все':
     full_df = full_df[full_df['Наименование на русском языке'] == kopf_filter].reset_index(drop=True)

print(full_df)

# H3 resolution
h3_resolution = 9

# Create H3 hexagons for each point in the dataframe
full_df['h3_index'] = full_df.apply(lambda row: h3.geo_to_h3(row.geometry.y, row.geometry.x, h3_resolution), axis=1)

# Aggregate the count of companies within each hexagon
hex_agg = full_df.groupby('h3_index').size().reset_index(name='company_count')

# Create polygons from H3 hexagons
hex_agg['geometry'] = hex_agg['h3_index'].apply(lambda x: Polygon(h3.h3_to_geo_boundary(x, geo_json=True)))

# Convert to GeoDataFrame
hex_gdf = gpd.GeoDataFrame(hex_agg, geometry='geometry')

# Calculate the color scale based on the company count
max_count = hex_gdf['company_count'].max()
hex_gdf['fill_color'] = hex_gdf['company_count'].apply(
    lambda x: [int(255 * (x / max_count)), 0, 255 - int(255 * (x / max_count)), 140]
)

# Toggle for elevation
if use_elevation:
    hex_gdf['elevation'] = hex_gdf['company_count']
else:
    hex_gdf['elevation'] = 0

# Create a Pydeck Layer
layer = pdk.Layer(
    "PolygonLayer",
    data=hex_gdf,
    get_polygon="geometry.coordinates",
    get_fill_color="fill_color",
    get_elevation="elevation",
    pickable=True,
    extruded=True,
    elevation_scale=50,
    elevation_range=[0, 3000],
)

# Define the view for the map
view_state = pdk.ViewState(
    longitude=76.95, latitude=43.25, zoom=10, pitch=50
)

# Render the map with Streamlit
st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state=view_state,
    layers=[layer],
    tooltip = {
    "html": "<b>{company_count}</b> количество компаний на локации",
    "style": {"background": "grey", "color": "white", "font-family": '"Helvetica Neue", Arial', "z-index": "10000"},
} 
))

# Display the count of companies in each hexagon
st.write(hex_gdf[['h3_index', 'company_count']])