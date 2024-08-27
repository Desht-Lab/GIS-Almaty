import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import json
import plotly.graph_objects as go

# Load the data
hexagon_gdf = pd.read_pickle('taxes.pkl').fillna(0)

st.title("Налоги Алматинской агломерации")
selected_taxes = st.selectbox("Выбрать год", ['2022','2021'])

# Toggle between logarithmic and absolute scale (default is logarithmic)
selected_scale = st.selectbox("Выбрать шкалу", ["Тиры",'Абсолютная','Логарифмическая'])

# Apply the selected year to the taxes column
hexagon_gdf['taxes'] = hexagon_gdf['y' + selected_taxes]

# Function to find the top company by taxes
def find_top_company(group):
    top_idx = group['taxes'].idxmax()  # Get the index of the max tax
    return pd.Series({
        'taxes': group['taxes'].sum(),
        'top_company': group.loc[top_idx, 'organization_name'],
        'top_taxes': group.loc[top_idx, 'taxes']
    })

# Group the data by geometry and find the top company and total taxes
result = hexagon_gdf.groupby('geometry').apply(find_top_company).reset_index()

# Format the taxes for hover text
result['hover_text'] = result.apply(
    lambda row: f"{row['top_company']}: {row['top_taxes']:,}", axis=1
)

if selected_scale == "Тиры":
    conditions = [
        (result['taxes'] <= 100000000),
        (result['taxes'] > 100000000) & (result['taxes'] <= 1000000000),
        (result['taxes'] > 1000000000) & (result['taxes'] <= 50000000000),
        (result['taxes'] > 50000000000) & (result['taxes'] <= 150000000000),
        (result['taxes'] > 150000000000)
    ]

    values = [1, 2, 3, 4, 5]

    result['tier'] = np.select(conditions, values)
    
    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(result, geometry='geometry')

    # Convert geometry to GeoJSON format
    geojson = json.loads(gdf.geometry.to_json())

    # Create the Plotly figure
    fig = go.Figure()

    fig.add_trace(go.Choroplethmapbox(
        geojson=geojson,
        locations=gdf.index,
        z=gdf['tier'],
        colorscale="Jet",
        marker_opacity=0.7,
        marker_line_width=0,
        text=gdf['hover_text'],
        colorbar=dict(
            title="Tax Tiers",
            tickvals=[1, 2, 3, 4, 5],
            ticktext=[
                "≤ 100M",
                "100M - 1B",
                "1B - 50B",
                "50B - 150B",
                "> 150B"
            ]
        )
    ))

    # Center map on Almaty city
    center_lat, center_lon = 43.536224, 76.938093

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=8,
        mapbox_center={"lat": center_lat, "lon": center_lon}
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    # Display the map in Streamlit
    st.plotly_chart(fig)

else:
# Apply logarithmic scale if selected
    if selected_scale == "Логарифмическая":
        result['taxes'] = np.log1p(result['taxes'])

    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(result, geometry='geometry')

    # Convert geometry to GeoJSON format
    geojson = json.loads(gdf.geometry.to_json())

    # Create the Plotly figure
    fig = go.Figure()

    fig.add_trace(go.Choroplethmapbox(
        geojson=geojson,
        locations=gdf.index,
        z=gdf['taxes'],
        colorscale="Plasma",
        marker_opacity=0.7,
        marker_line_width=0,
        text=gdf['hover_text']
    ))

    # Center map on Almaty city
    center_lat, center_lon = 43.536224, 76.938093

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=8,
        mapbox_center={"lat": center_lat, "lon": center_lon}
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    # Display the map in Streamlit
    st.plotly_chart(fig)
