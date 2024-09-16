import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import json
import numpy as np
import geopandas as gpd

# Load the data
long_data = pd.read_pickle('long_rca_original_sections.pkl')
rca_df = pd.read_pickle('rca_original_sections.pkl')

# Create pivot table for rca_df_emp
rca_df_emp = long_data.pivot(index='asigned_cluster', columns='industry', values='employment').reset_index()



# Mapping cluster numbers to names
clusters = {
    0: "Сельский",
    1: "Мкр. Нур Алатау",
    3: "Узынагаш",
    2: "Периферийный",
    4: "Талгар",
    5: "Каскелен",
    6: "Мкр. Горный Гигант",
    7: "Есик",
    8: "Суюнбая и Майлина",
    9: "Отеген батыра",
    10: "Микрорайоны и Орбита",
    11: "ул. Рыскулова, от Бокейханова до Суюнбая",
    12: "Конаев",
    13: "Розыбакиева",
    14: "Толе би-Саина",
    15: "пр. Райымбека, от Розыбакиева до Саяхата",
    16: "мкр. Коктем-1",
    17: "пр. Достык",
    18: "Золотой квадрат"
}

# List of modified column names
modified_column_names = ['A-Сельское, лесное и рыбное хозяйство',
       'B-Горнодобывающая промышленность и разработка карьеров',
       'C-Обрабатывающая промышленность',
       'D-Снабжение электроэнергией, газом, паром, горячей водой и  кондиционированным воздухом',
       'E-Водоснабжение; водоотведение; сбор, обработка и удаление отходов, деятельность по ликвидации загрязнений',
       'F-Строительство',
       'G-Оптовая и розничная торговля; ремонт автомобилей и мотоциклов',
       'H-Транспорт и складирование',
       'I-Предоставление услуг по проживанию и питанию',
       'J-Информация и связь', 'K-Финансовая и страховая деятельность',
       'L-Операции с недвижимым имуществом',
       'M-Профессиональная, научная и техническая деятельность',
       'N-Деятельность в области административного и вспомогательного обслуживания',
       'O-Государственное управление и оборона; обязательное  социальное обеспечение',
       'P-Образование',
       'Q-Здравоохранение и социальное обслуживание населения',
       'R-Искусство, развлечения и отдых',
       'S-Предоставление прочих видов услуг']

# Streamlit multiselect widget to choose columns to include in the radar chart
st.markdown('''<style>.streamlit-secondary-button {background-color: transparent; color: white; padding: 0.25em 0.75em; text-align: center; font-size: 16px; font-weight: 400; line-height: 1.6; border: 1px solid #0068c9; border-radius: 0.25rem; text-decoration: none; display: inline-block; cursor: pointer; transition: all 0.2s ease;} .streamlit-secondary-button:hover {background-color: #0068c9; color: white;}</style>''', unsafe_allow_html=True)

st.markdown(f'''
    <a href="https://desht-lab-gis-almaty-rcafilterdetailed-lwlizw.streamlit.app/" target="_self" class="streamlit-secondary-button">
        Детальнее
    </a>
''', unsafe_allow_html=True)

selected_columns = st.selectbox("Выбрать отрасль", modified_column_names)

rca_gdf = gpd.GeoDataFrame(rca_df, geometry='geometry')

# Calculate the percentage of employment for each industry in a cluster
rca_df_emp_percent = rca_df_emp.set_index('asigned_cluster')
rca_df_emp_percent = rca_df_emp_percent.div(rca_df_emp_percent.sum(axis=1), axis=0) * 100

# Add a checkbox to filter out industry-cluster pairs < 5%
filter_checkbox = st.checkbox('Убрать индустрии-кластеры < 5%', value=True)

if filter_checkbox:
    # Apply the filter by setting values below 5% to NaN
    rca_df_emp_percent = rca_df_emp_percent.applymap(lambda x: np.nan if x < 5 else x)

# Display the percentage DataFrame
rca_df_emp_percent.reset_index(inplace=True)


# If a specific industry is selected for the radar chart
if selected_columns:
    section_filter = rca_df_emp_percent[['asigned_cluster', selected_columns]].dropna()[['asigned_cluster']]
    section_filter = section_filter.rename(columns = {'asigned_cluster':'target_rca'})

    print(section_filter)
    # Map cluster numbers to names
    rca_df['cluster_name'] = rca_df['asigned_cluster'].map(clusters)
    rca_df = rca_df.merge(section_filter, left_on = 'asigned_cluster', right_on = 'target_rca', how = 'left', validate = '1:1')
    rca_df['target_rca']= np.where(rca_df['target_rca'].isna(), 0, rca_df[selected_columns])

    # Prepare custom data for hover information
    customdata = np.stack((rca_df['asigned_cluster'], rca_df['cluster_name'],rca_df[selected_columns] ), axis=-1)

    # Convert merged GeoDataFrame's geometry to GeoJSON
    geojson = json.loads(rca_gdf.geometry.to_json())

    # Initialize Plotly Figure
    fig = go.Figure()

    # Assuming the first polygon's centroid is a good center point for initial view
    center_lat, center_lon = 43.270507, 76.914576

    def create_colorscale(min_z, max_z):
        # Adjust breakpoints based on the min and max of z
        if max_z == min_z:
            colorscale = [[0, 'grey'], [1, 'grey']]
        else:
            mid_point = 0.9999999
            grey_stop = (mid_point - min_z) / (max_z - min_z)
            white_stop = (mid_point - min_z + 0.0000001) / (max_z - min_z)
            colorscale = [
                [0, 'grey'],           # Grey at min_z
                [grey_stop, 'grey'],   # Grey until just before 1
                [white_stop, 'white'], # White just after 1
                [1, '#376c8a']         # Custom color at max_z
            ]
        return colorscale

    # Add the initial trace with the custom colorscale
    z_values = rca_df['target_rca']
    min_z, max_z = z_values.min(), z_values.max()
    custom_colorscale = create_colorscale(min_z, max_z)

    fig.add_trace(go.Choroplethmapbox(
        geojson=geojson,
        locations=rca_df.index,
        z=z_values,
        colorscale=custom_colorscale,
        marker_opacity=0.5,
        marker_line_width=1,
        customdata=customdata,
        hovertemplate=(
            'Кластерный номер: %{customdata[0]}<br>'
            'Название кластера: %{customdata[1]}<br>'
            'Значение: %{customdata[2]}<extra></extra>'
        )
    ))

    # Update layout with OpenStreetMap style and centering on the first polygon
    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=11,
        mapbox_center={"lat": center_lat, "lon": center_lon}
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
                      updatemenus=[dict(active=0, font=dict(family="Gotham", size=11))])

    # Display the figure in Streamlit
    st.plotly_chart(fig)

else:
    st.warning("Please select at least one category to display the radar chart.")
