import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Load the RCA DataFrame
rca_df = pd.read_pickle('rca.pkl')

# Modified column names (categories)
modified_column_names = ['A-Сельское, лесное и рыбное хозяйство',
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
       'J-Информация и связь', 'K-Финансовая и страховая деятельность',
       'L-Операции с недвижимым имуществом',
       'M-Профессиональная, научная и техническая деятельность',
       'N-Деятельность в области административного обслуживания',
       'O-Государственное управление и оборона', 'P-Высшее образование',
       'P-Довузовское образование', 'R-Искусство, развлечения и отдых',
       'S-Предоставление прочих видов услуг',
       'Q-Здравоохранение и социальное обслуживание населения (другие)',
       'Q-Здравоохранение и социальное обслуживание населения (крупные, государственные)',
       'Q-Здравоохранение и социальное обслуживание населения (частные)']

# Select any number of clusters
selected_clusters = st.multiselect('Выберите кластеры:', rca_df['asigned_cluster'].unique(), default=rca_df['asigned_cluster'].unique()[:2])

if not selected_clusters:
    st.warning("Выберите хотябы 1 кластер")
else:
    # Filter data for the selected clusters
    filtered_df = rca_df[rca_df['asigned_cluster'].isin(selected_clusters)]

    # Create a horizontal bar chart
    bar_fig = go.Figure()

    # Add bars for each selected cluster
    for cluster in selected_clusters:
        cluster_data = filtered_df[filtered_df['asigned_cluster'] == cluster]
        bar_fig.add_trace(go.Bar(
            y=modified_column_names,  # Categories on the y-axis
            x=cluster_data[modified_column_names].values[0],  # RCA values on the x-axis
            orientation='h',  # Horizontal bars
            name=f'Cluster {cluster}'
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
    bar_fig.update_layout(
        title="Сравнение кластеров по RCA",
        xaxis_title="RCA",
        yaxis_title="Секции",
        font=dict(
            family="Gotham, sans-serif",  # Gotham font with a fallback to sans-serif
            size=14  # Increased font size for PowerPoint visibility
        ),
        showlegend=True,
        barmode='group'  # Group the bars side by side
    )

    # Display the bar chart in Streamlit
    st.plotly_chart(bar_fig)
