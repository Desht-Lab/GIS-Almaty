import pandas as pd
import plotly.graph_objects as go
import streamlit as st

rca_df = pd.read_pickle('rca.pkl')
modified_column_names = ['A-Сельское, лесное и рыбное хозяйство',
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
       'P-Довузовское образование', 'R-Искусство, развлечения и отдых',
       'S-Предоставление прочих видов услуг',
       'Q-Здравоохранение и социальное обслуживание населения (другие)',
       'Q-Здравоохранение и социальное обслуживание населения (крупные, государственные)',
       'Q-Здравоохранение и социальное обслуживание населения (частные)']

# Streamlit multiselect widget to choose columns to include in the radar chart
selected_columns = st.multiselect('Select categories to include in the radar chart:', modified_column_names,  [])

import textwrap

def wrap_text(text, max_width=20):
    """Wraps text at the end of words if it exceeds max_width characters."""
    return '<br>'.join(textwrap.wrap(text, width=max_width, break_long_words=False))

def create_radar_chart(rca_df, selected_columns, cluster_color='#376c8a'):
    if not selected_columns:
        st.warning("Please select at least one category to display the radar chart.")
        return

    # Wrap column names for better display
    wrapped_columns = [wrap_text(col) for col in selected_columns]

    # Create radar chart traces for each cluster using the index as the label
    radar_fig = go.Figure()
    
    for index, row in rca_df.iterrows():
        radar_fig.add_trace(go.Scatterpolar(
            r=row[selected_columns].values,
            theta=wrapped_columns,
            fill='toself',
            name=str(row['asigned_cluster']),  # Using the cluster label
            line=dict(color=cluster_color, width=4),  # Thicker lines
            marker=dict(size=10)  # Larger markers
        ))
    
    # Add a trace to highlight RCA = 1
    radar_fig.add_trace(go.Scatterpolar(
        r=[1] * len(selected_columns),
        theta=wrapped_columns,
        mode='lines',
        line=dict(color='red', dash='dash', width=4),  # Thicker dashed line
        name='RCA = 1'
    ))
    
    # Customize the layout
    radar_fig.update_layout(
        font=dict(
            family="Gotham, sans-serif",  # Gotham font with a fallback to sans-serif
            size=18  # Increased font size for PowerPoint visibility
        ),
        polar=dict(
            radialaxis=dict(visible=True),
        ),
        showlegend=True,
        title="RCA Comparison Across Clusters"
    )
    
    st.plotly_chart(radar_fig)

# Call the function with the selected columns
create_radar_chart(rca_df, selected_columns, cluster_color='#376c8a')
