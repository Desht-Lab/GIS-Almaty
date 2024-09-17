import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Load the RCA DataFrame
rca_df = pd.read_pickle('rca_original_sections.pkl')

# Modified column names (categories)
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

# Cluster dictionary
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

# Map the cluster IDs to formatted strings (both key and value)
cluster_options = [f'{key} - {value}' for key, value in clusters.items()]
# Select any number of clusters
selected_clusters = st.multiselect('Выберите кластеры:', cluster_options, default=cluster_options[:2])

if not selected_clusters:
    st.warning("Выберите хотя бы 1 кластер")
else:
    # Extract the selected cluster keys from the selected options
    selected_cluster_keys = [int(option.split(' - ')[0]) for option in selected_clusters]

    # Filter data for the selected clusters
    filtered_df = rca_df[rca_df['asigned_cluster'].isin(selected_cluster_keys)]

    # Create a horizontal bar chart
    bar_fig = go.Figure()

    # Add bars for each selected cluster
    for cluster_key in selected_cluster_keys:
        cluster_data = filtered_df[filtered_df['asigned_cluster'] == cluster_key]
        bar_fig.add_trace(go.Bar(
            y=modified_column_names,  # Categories on the y-axis
            x=cluster_data[modified_column_names].values[0],  # RCA values on the x-axis
            orientation='h',  # Horizontal bars
            name=f'Кластер {clusters[cluster_key]}'
        ))

    # Add a dotted red line at RCA = 1
    bar_fig.add_trace(go.Scatter(
        y=modified_column_names,
        x=[1] * len(modified_column_names),
        mode='lines',
        line=dict(color='red', dash='dash', width=2),
        name='RCA = 1'
    ))

    # Customize the layout
    max_height = 600  # Maximum height for the chart
    bar_fig.update_layout(
        title=dict(
            text="Сравнение кластеров по RCA",
            font=dict(size=24)  # Increased title font size
        ),
        xaxis_title="RCA",
        yaxis_title="",
        font=dict(
            family="Gotham, sans-serif",  # Gotham font with a fallback to sans-serif
            size=14  # General font size
        ),
        yaxis=dict(
            tickfont=dict(size=16),  # Increased font size for y-axis labels
            automargin=True  # Adjust margins to accommodate larger font size
        ),
        showlegend=True,
        barmode='group',  # Group the bars side by side
        height=min(50 * len(modified_column_names), max_height)  # Adjust height
    )

    # Display the bar chart in a scrollable container if necessary
    chart_container = st.container()
    with chart_container:
        st.plotly_chart(bar_fig, use_container_width=True)
