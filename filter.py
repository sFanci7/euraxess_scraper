from dateutil import parser
import streamlit as st
import pandas as pd

# Load the CSV file
df = pd.read_csv('output/jobs_20250713.csv')

# Create boolean columns for each profile
df['R1'] = df['profile'].str.contains('R1', case=False, na=False)
df['R2'] = df['profile'].str.contains('R2', case=False, na=False)
df['R3'] = df['profile'].str.contains('R3', case=False, na=False)
df['R4'] = df['profile'].str.contains('R4', case=False, na=False)

# Function to extract relevant items from the 'field' column


def extract_relevant_items(s):
    try:
        items = [item.strip() for item in s.split(';')]
    except:
        return None, None
    class_1 = []
    class_2 = []
    for i in range(len(items)):
        curr = items[i]
        prev = items[i - 1] if i > 0 else ''
        next = items[i + 1] if i < len(items) - 1 else ''

        if next == '»':
            class_1.append(curr)
        elif prev == '»':
            class_2.append(curr)
        elif prev != '»' and next != '»' and curr != '»':
            class_1.append(curr)
    return ','.join(set(class_1)), ','.join(set(class_2))


# Apply the extraction function to the 'field' column
df['field_1'], df['field_2'] = zip(*df['field'].apply(extract_relevant_items))

# Convert 'application_deadline' to datetime, handling cases where it might be NaN
df['application_deadline'] = df['application_deadline'].apply(lambda x: parser.parse(x.split('(')[0].strip()) if pd.notnull(x) else None)

# Create lists of unique fields and countries
all_main_fields = []
all_sub_fields = []
for i in range(len(df)):
    if pd.notnull(df['field_1'][i]):
        all_main_fields.extend(df['field_1'][i].split(','))
    if pd.notnull(df['field_2'][i]):
        all_sub_fields.extend(df['field_2'][i].split(','))

all_main_fields = sorted(set(all_main_fields), key=lambda x: x.lower())
all_sub_fields = sorted(set(all_sub_fields), key=lambda x: x.lower())

# Create boolean columns for each unique field in field_1
new_columns = {
    _: df['field_1'].str.contains(_, case=False, na=False)
    for _ in all_main_fields
}
df = pd.concat([df, pd.DataFrame(new_columns)], axis=1)

new_columns = {
    _: df['field_2'].str.contains(_, case=False, na=False)
    for _ in all_sub_fields
}
df = pd.concat([df, pd.DataFrame(new_columns)], axis=1)

# Selection of unique countries and profiles
all_countries = sorted(df['country'].dropna().unique().tolist(), key=lambda x: x.lower())
all_profiles = ['R1', 'R2', 'R3', 'R4']

# Streamlit app setup
st.set_page_config(page_title="Euraxess Data", layout="wide")

# Sidebar for filters
with st.sidebar:
    st.header("Filters")

    selected_countries = st.multiselect("Country", options=all_countries)
    selected_profiles = st.multiselect("Profile", options=all_profiles)
    selected_fields = st.multiselect("Field", options=all_main_fields)
    selected_sub_fields = st.multiselect("Sub-field", options=all_sub_fields)

# Filter the DataFrame based on selections
df_filtered = df.copy()
if selected_countries:
    df_filtered = df_filtered[df_filtered['country'].isin(selected_countries)]

if selected_profiles:
    df_filtered = df_filtered[df_filtered[selected_profiles].any(axis=1)]

if selected_fields:
    df_filtered = df_filtered[df_filtered[selected_fields].any(axis=1)]

if selected_sub_fields:
    df_filtered = df_filtered[df_filtered[selected_sub_fields].any(axis=1)]

# 显示筛选后的数据
show_columns = ['country', 'university', 'title',  'link', 'application_deadline',  'posted_on',
                'description', 'department', 'location', 'funding_program', 'type', 'profile']
st.subheader("Results")
st.write(f"{len(df_filtered)} rows")
st.dataframe(df_filtered[show_columns], use_container_width=True, height=500, column_config={
    'link': st.column_config.LinkColumn()
})
