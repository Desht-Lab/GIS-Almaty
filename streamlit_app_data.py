import geopandas as gpd
import pandas as pd
import h3
from shapely.geometry import Polygon
import numpy as np



# Load your data
fields = pd.read_excel('группировка отраслей.xlsx')
almaty_XY = pd.read_pickle('finalAlmatyFixedForCityClustering.pkl')
almatyAglo_XY = pd.read_pickle('finalAgloNewCleanWhole-Sana.pkl')
almaty_XY = pd.concat([almatyAglo_XY, almaty_XY])

fields['oked5'] = fields['oked5'].astype(str).str.zfill(5)
almaty_XY = almaty_XY.merge(fields[['oked5', 'Fields', 'Desc']], left_on="oked",
                            right_on="oked5", how='left', validate="m:1")

full_df = almaty_XY[~almaty_XY['x'].isna()]
full_df = gpd.GeoDataFrame(
    full_df, geometry=gpd.points_from_xy(full_df.x, full_df.y))

# One-hot encode the 'Desc' column
df_one_hot = pd.get_dummies(full_df, columns=['Desc'])

# Replace the 1s in the one-hot encoded columns with the corresponding 'emp' values
for col in df_one_hot.columns:
    if (col.startswith('Desc_')):
        section = col.split('_')[-1]
        df_one_hot[col] = df_one_hot[col] * full_df['emp']

# Drop the original 'emp' column
df_one_hot = df_one_hot.drop(columns=['emp'])

# Aggregate by 'x' and 'y' columns
columns_to_sum = [col for col in df_one_hot.columns if col.startswith('Desc_')]

desc_values =  [col.split('_')[1] for col in columns_to_sum]

# Create a DataFrame to sort
temp_df = pd.DataFrame({
    'columns_to_sum': columns_to_sum,
    'Desc': desc_values
})

# Merge with fields DataFrame to get the corresponding grand_section_code
merged_df = temp_df.merge(fields[['Desc', 'grand_section_code']], on='Desc', how='left')

# Sort by grand_section_code and then by columns_to_sum
sorted_df = merged_df.sort_values(by=['grand_section_code', 'columns_to_sum'])

# Extract the sorted columns_to_sum
sorted_columns_to_sum = sorted_df['columns_to_sum'].tolist()
res,ind = np.unique(sorted_columns_to_sum, return_index = True)
sorted_columns_to_sum = res[np.argsort(ind)]

df_aggregated = df_one_hot.groupby(['x', 'y'])[sorted_columns_to_sum].sum().reset_index()

def h3_hexagon_polygon(hex_id):
    """Convert H3 hex id to a Shapely polygon."""
    boundary = h3.h3_to_geo_boundary(hex_id, geo_json=True)
    return Polygon(boundary)

# Step 1: Choose an appropriate resolution
resolution = 9

# Step 2: Convert points to H3 indices
df_aggregated['h3_index'] = df_aggregated.apply(lambda row: h3.geo_to_h3(float(row.y), float(row.x), resolution), axis=1)

# Step 3: Aggregate data based on H3 indices
hexagon_gdf = df_aggregated.groupby('h3_index')[sorted_columns_to_sum].sum().reset_index()

# Step 4: Convert H3 indices to hexagon polygons
hexagon_gdf['geometry'] = hexagon_gdf['h3_index'].apply(h3_hexagon_polygon)

# Convert to GeoDataFrame
hexagon_gdf = gpd.GeoDataFrame(hexagon_gdf, geometry='geometry')

# Simplify column names
hexagon_gdf.columns = [
    col.split('_')[1] if '_' in col else col
    for col in hexagon_gdf.columns
]
modified_column_names = [col.split('_')[1] for col in sorted_columns_to_sum]
hexagon_gdf['Все'] = hexagon_gdf[modified_column_names].sum(axis = 1)
hexagon_gdf['empl'] = hexagon_gdf[modified_column_names].sum(axis = 1)
merged_gdf_comp = gpd.sjoin(full_df, hexagon_gdf, how="inner", predicate='within', lsuffix='companies', rsuffix='right' )

# Aggregate top 5 companies by employment for each hexagon
def top_5_companies(hexagon_gdf):
    top_5 = hexagon_gdf.nlargest(5, 'emp')
    return ',<br>'.join([f"{row['organization_name']} ({row['emp']})"  for _, row in top_5.iterrows()])

company_agg = merged_gdf_comp.groupby('index').apply(top_5_companies).reset_index()
company_agg.columns = ['index', 'top_5_companies']

# Merge the aggregated company names back to the original GeoDataFrame
hexagon_gdf = hexagon_gdf.reset_index()

hexagon_gdf = hexagon_gdf.merge(company_agg, left_on='index', right_on='index', how='left')
hexagon_gdf['top_5_companies'] = hexagon_gdf['top_5_companies'].fillna('No companies')
modified_column_names.insert(0, 'Все')

hexagon_gdf.to_pickle('descriptive_data_app.pkl')