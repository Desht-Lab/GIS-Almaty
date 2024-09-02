import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import json

# Load the data
rca_df = pd.read_pickle('rca.pkl')
modified_column_names =['A-Сельское, лесное и рыбное хозяйство',
       'B-Горнодобывающая промышленность и разработка карьеров',
       'C-Обрабатывающая промышленность - Базовый передел',
       'C-Обрабатывающая промышленность - Интенсивная (технологически)',
       'C-Обрабатывающая промышленность - Неинтенсивная (технологически)',
       'D-Снабжение электроэнергией, газом и пр.',
       'E-Водоснабжение; сбор, обработка и удаление отходов',
       'F-Строительство',
       '45-Оптовая и розничная торговля автомобилями и мотоциклами и их ремонт',
       '46-Оптовая торговля, за исключением торговли автомобилями и мотоциклами',
       '47-Розничная торговля - 2000 кв.м и выше',
       '47-Розничная торговля - менее 2000 кв.м',
       '47-Розничная торговля - площадь не уточнена',
       'H-Транспорт и складирование',
       'I-Предоставление услуг по проживанию и питанию',
       'J-Информация и связь', 'K-Финансовая и страховая деятельность',
       'L-Операции с недвижимым имуществом',
       'M-Профессиональная, научная и техническая деятельность',
       'N-Деятельность в области административного обслуживания',
       'O-Государственное управление и оборона', 'P-Высшее образование',
       'P-Довузовское образование',
       '900-Деятельность в области творчества, искусства и развлечений',
       '910-Деятельность библиотек, архивов, музеев и прочая деятельность в области культуры',
       '920-Деятельность по организации азартных игр и заключению пари',
       '931-Деятельность в области спорта',
       '932-Деятельность по организации отдыха и развлечений',
       'S-Предоставление прочих видов услуг',
       'Q-Здравоохранение и социальное обслуживание населения (другие)',
       'Q-Здравоохранение и социальное обслуживание населения (крупные, государственные)',
       'Q-Здравоохранение и социальное обслуживание населения (частные)']
# Streamlit multiselect widget to choose columns to include in the radar chart
selected_columns = st.selectbox("Выбрать отрасль", modified_column_names)

# Check if any columns are selected
if selected_columns:
    # Convert merged GeoDataFrame's geometry to GeoJSON
    geojson = json.loads(rca_df.geometry.to_json())

    # Initialize Plotly Figure
    fig = go.Figure()

    # Assuming the first polygon's centroid is a good center point for initial view
    center_lat, center_lon = 43.536224, 76.938093

    def create_colorscale(min_z, max_z):
        # Adjust breakpoints based on the min and max of z
        if max_z == min_z:  # Handle the case where all values are the same
            colorscale = [[0, 'grey'], [1, 'grey']]
        else:
            mid_point = 0.99
            grey_stop = (mid_point - min_z) / (max_z - min_z)
            white_stop = (mid_point - min_z + 0.00001) / (max_z - min_z)#
            colorscale = [
                [0, 'grey'],           # Grey at min_z
                [grey_stop, 'grey'],   # Grey until just before 1
                [white_stop, 'white'], # White just after 1
                [1, '#376c8a']             # Red at max_z
            ]
        return colorscale

    # Add the initial trace with the custom colorscale
    z_values = rca_df[selected_columns].round(2)
    min_z, max_z = z_values.min(), z_values.max()
    custom_colorscale = create_colorscale(min_z, max_z)

    fig.add_trace(go.Choroplethmapbox(
        geojson=geojson,
        locations=rca_df.index,
        z=z_values,
        colorscale=custom_colorscale,
        marker_opacity=0.5,
        marker_line_width=1
    ))

    # Create buttons to switch between different columns
    

    # Update layout with OpenStreetMap style and centering on the first polygon
    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=8,
        mapbox_center={"lat": center_lat, "lon": center_lon}
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
                      updatemenus=[dict(active=0, font=dict(family="Gotham", size=11))])

    # Display the figure in Streamlit
    st.plotly_chart(fig)
else:
    st.warning("Please select at least one category to display the radar chart.")
