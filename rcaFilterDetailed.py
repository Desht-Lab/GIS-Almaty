import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import json
import numpy as np

# Load the data
rca_df = pd.read_pickle('rcaDetailed.pkl')
modified_column_names =['A-Сельское, лесное и рыбное хозяйство',
       'B-Горнодобывающая промышленность и разработка карьеров',
       'C-Обрабатывающая промышленность Базовый передел',
       'C-Обрабатывающая промышленность Интенсивная (технологически)',
       'C-Обрабатывающая промышленность Неинтенсивная (технологически)',
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
       '58/59/60 - Медиа, издательская деятельность',
       '61-Телекоммуникации', '62/63 - IT',
       '64-Финансовое посредничество, кроме страхования и пенсионного обеспечения',
       '65-Страхование, перестрахование и пенсионное обеспечение, кроме обязательного социального обеспечения',
       '66-Вспомогательная деятельность в сфере финансовых услуг и страхования',
       'L-Операции с недвижимым имуществом',
       'M-Деятельность в области права и бухгалтерского учета; Деятельность головных компаний; консультирование по вопросам управления',
       'M-Профессиональная, научная и техническая деятельность (остальные)',
       'N-Деятельность в области административного обслуживания',
       'O-Государственное управление и оборона', 'P-Высшее образование',
       'P-Довузовское образование', 'R-Искусство, развлечения и отдых',
       'S-Предоставление прочих видов услуг',
       'Q-Здравоохранение и социальное обслуживание населения (другие)',
       'Q-Здравоохранение и социальное обслуживание населения (крупные, государственные)',
       'Q-Здравоохранение и социальное обслуживание населения (частные)']



clusters = {
    0: "Сельский",
    1: "Мкр. Нур Алатау",
    2: "Узынагаш",
    3: "Периферийный",
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

selected_columns = st.selectbox("Выбрать отрасль", modified_column_names)

if selected_columns:
    # Map cluster numbers to names
    rca_df['cluster_name'] = rca_df['asigned_cluster'].map(clusters)

    # Prepare custom data for hover information
    customdata = np.stack((rca_df['asigned_cluster'], rca_df['cluster_name']), axis=-1)

    # Convert merged GeoDataFrame's geometry to GeoJSON
    geojson = json.loads(rca_df.geometry.to_json())

    # Initialize Plotly Figure
    fig = go.Figure()

    # Assuming the first polygon's centroid is a good center point for initial view
    center_lat, center_lon =43.270507, 76.914576

    def create_colorscale(min_z, max_z):
        # Adjust breakpoints based on the min and max of z
        if max_z == min_z:  # Handle the case where all values are the same
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
    z_values = rca_df[selected_columns]
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
            'Значение: %{z}<extra></extra>'
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