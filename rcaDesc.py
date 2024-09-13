import geopandas as gpd
from shapely.ops import unary_union
import pandas as pd
import json
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import numpy as np

joined_gdf = pd.read_pickle('joined_gdfDesc.pkl')

section_name_mapping = {'A': 'A-Сельское, лесное и рыбное хозяйство',
 'B': 'B-Горнодобывающая промышленность и разработка карьеров',
 'C': 'C-Обрабатывающая промышленность',
 'D': 'D-Снабжение электроэнергией, газом, паром, горячей водой и  кондиционированным воздухом',
 'E': 'E-Водоснабжение; водоотведение; сбор, обработка и удаление отходов, деятельность по ликвидации загрязнений',
 'F': 'F-Строительство',
 'G': 'G-Оптовая и розничная торговля; ремонт автомобилей и мотоциклов',
 'H': 'H-Транспорт и складирование',
 'I': 'I-Предоставление услуг по проживанию и питанию',
 'J': 'J-Информация и связь',
 'K': 'K-Финансовая и страховая деятельность',
 'L': 'L-Операции с недвижимым имуществом',
 'M': 'M-Профессиональная, научная и техническая деятельность',
 'N': 'N-Деятельность в области административного и вспомогательного обслуживания',
 'O': 'O-Государственное управление и оборона; обязательное  социальное обеспечение',
 'P': 'P-Образование',
 'Q': 'Q-Здравоохранение и социальное обслуживание населения',
 'R': 'R-Искусство, развлечения и отдых',
 'S': 'S-Предоставление прочих видов услуг'}
section_codes =dict(sorted(section_name_mapping.items()))
# Assuming 'joined_gdf' is your GeoDataFrame
joined_gdf['cluster_mean_emp'] = joined_gdf.groupby('AC19')['emp'].transform('mean')
joined_gdf['cluster_total_emp'] = joined_gdf.groupby('AC19')['emp'].transform('sum')
joined_gdf['cluster_total_emp'] = joined_gdf['cluster_total_emp'].astype(int)

# Streamlit selectors for AC19
st.sidebar.title('Выбор кластеров')
selected_ac1 = st.sidebar.selectbox('Выберите 1ый кластер', np.sort(joined_gdf['AC19'].unique()))
selected_ac2 = st.sidebar.selectbox('Выберите 2ой кластер', np.sort(joined_gdf['AC19'].unique()))

mean1 = joined_gdf[joined_gdf['AC19'] == selected_ac1].cluster_mean_emp.iloc[0]
mean2 = joined_gdf[joined_gdf['AC19'] == selected_ac2].cluster_mean_emp.iloc[0]

total1 = joined_gdf[joined_gdf['AC19'] == selected_ac1].cluster_total_emp.iloc[0]
total2 = joined_gdf[joined_gdf['AC19'] == selected_ac2].cluster_total_emp.iloc[0]
# Calculate overall shares
overall_shares = {}
for section_code, section_name in section_name_mapping.items():
    overall_shares[section_code] = (
        joined_gdf[f"grand_section_code_{section_code}_hex"].sum() / joined_gdf['emp'].sum() * 100
    )
overall_shares_list = [overall_shares[code] for code in section_name_mapping.keys()]

# Calculate shares for the selected clusters
def calculate_cluster_shares(cluster_id):
    cluster_data = joined_gdf[joined_gdf['AC19'] == cluster_id]
    cluster_total_emp = cluster_data['cluster_total_emp'].iloc[0]
    cluster_shares = [
        cluster_data[f"grand_section_code_{section_code}_hex"].sum() / cluster_total_emp * 100
        for section_code in section_name_mapping.keys()
    ]
    return cluster_shares

# Get shares for selected clusters
cluster1_shares = calculate_cluster_shares(selected_ac1)
cluster2_shares = calculate_cluster_shares(selected_ac2)

# Prepare data for the bar chart
fig = go.Figure()

# Add overall bar
fig.add_trace(go.Bar(
    x=list(section_name_mapping.keys()),
    y=overall_shares_list,
    name='Всего',
    marker=dict(color='#828388')
))

# Add bar for the first selected cluster
fig.add_trace(go.Bar(
    x=list(section_name_mapping.keys()),
    y=cluster1_shares,
    name=f'Кластер {selected_ac1}',
    marker=dict(color='#376c8a')
))

# Add bar for the second selected cluster
fig.add_trace(go.Bar(
    x=list(section_name_mapping.keys()),
    y=cluster2_shares,
    name=f'Кластер {selected_ac2}',
    marker=dict(color='#c59f72')  # You can change the color if needed
))

# Update layout
fig.update_layout(
    title='Сравнение доли секций по кластеру',
    xaxis_title='Код секции',
    yaxis_title='%',
    hovermode='closest',
    barmode='group'  # Grouped bars
)

st.markdown("Средняя условная занятость кластера " + str(selected_ac1) + ": " + str(round(mean1,2)) + \
            '''  
            Средняя условная занятость кластера ''' + str(selected_ac2) + ": " + str(round(mean2,2)))
st.markdown('''Общая условная занятость кластера'''  + str(selected_ac1) + ''': ''' + f"{total1:,.0f}".replace(",", " ")+ \
            '''  
            Общая условная занятость кластера ''' + str(selected_ac2) + ": " + f"{total2:,.0f}".replace(",", " ")
)
# Convert figure to HTML and append to the list
# Display the figure in Streamlit
st.plotly_chart(fig)
   