import streamlit as st
import pandas as pd
import altair as alt

# Enable full rendering
alt.data_transformers.enable('vegafusion')
alt.data_transformers.enable('default', max_rows=100000)

# Load data
df = pd.read_csv('listings.csv')
df['price'] = df['price'].replace('[\$,]', '', regex=True).astype(float)

# --- Sidebar filters ---
st.sidebar.header("Filter Listings")

# Neighborhood filter
neighborhoods = sorted(df['neighbourhood_cleansed'].dropna().unique())
selected_neighborhood = st.sidebar.selectbox("Select a neighborhood", ['All'] + neighborhoods)

# Price slider
min_price = int(df['price'].min())
max_price = int(df['price'].max())
price_range = st.sidebar.slider("Select price range", min_price, min(1000, max_price), (50, 500))

# Filter data based on selections
filtered_df = df.copy()
if selected_neighborhood != 'All':
    filtered_df = filtered_df[filtered_df['neighbourhood_cleansed'] == selected_neighborhood]

filtered_df = filtered_df[(filtered_df['price'] >= price_range[0]) & (filtered_df['price'] <= price_range[1])]

# --- Chart 1: Median Price by Neighborhood ---
st.subheader("Median Price by Neighborhood")
price_by_n = df.groupby('neighbourhood_cleansed')['price'].median().reset_index()
chart1 = alt.Chart(price_by_n).mark_bar().encode(
    x=alt.X('price:Q', title='Median Nightly Price ($)'),
    y=alt.Y('neighbourhood_cleansed:N', sort='-x', title='Neighborhood'),
    tooltip=['neighbourhood_cleansed', 'price']
).properties(width=600, height=400)
st.altair_chart(chart1)

# --- Chart 2: Room Type Distribution ---
st.subheader("Room Type Distribution and Prices")
room_chart = alt.Chart(filtered_df).mark_boxplot(extent='min-max').encode(
    x='room_type:N',
    y='price:Q',
    color='room_type:N'
).properties(width=400, height=300)

count_chart = alt.Chart(filtered_df).mark_bar(opacity=0.5).encode(
    x='room_type:N',
    y='count():Q',
    color='room_type:N'
)

st.altair_chart(count_chart & room_chart)

# --- Chart 3: Reviews vs. Revenue with Brushing ---
st.subheader("Reviews vs. Estimated Revenue (Past Year)")

# Handle missing or extreme values
filtered_rev = filtered_df[
    (filtered_df['number_of_reviews'] < 300) &
    (filtered_df['estimated_revenue_l365d'] < 100000)
]

brush = alt.selection_interval()

scatter = alt.Chart(filtered_rev).mark_circle(opacity=0.5).encode(
    x='number_of_reviews:Q',
    y='estimated_revenue_l365d:Q',
    tooltip=['name', 'number_of_reviews', 'estimated_revenue_l365d'],
    color=alt.condition(brush, alt.value('steelblue'), alt.value('lightgray'))
).add_params(brush)

regression = scatter.transform_regression(
    'number_of_reviews', 'estimated_revenue_l365d'
).mark_line(color='red')

st.altair_chart((scatter + regression).properties(width=600, height=400))

# --- Chart 4: Median Price by Host Location ---
st.subheader("Median Price by Host Location (Top 20 Locations)")

host_prices = df.copy()
host_prices = host_prices.dropna(subset=['host_location'])

top_locations = host_prices['host_location'].value_counts().nlargest(20).index
filtered_hosts = host_prices[host_prices['host_location'].isin(top_locations)]

median_price_by_host = filtered_hosts.groupby('host_location')['price'].median().reset_index()

chart4 = alt.Chart(median_price_by_host).mark_bar().encode(
    x=alt.X('price:Q', title='Median Price ($)'),
    y=alt.Y('host_location:N', sort='-x', title='Host Location'),
    tooltip=['host_location', 'price']
).properties(
    width=600,
    height=500,
    title='Median Airbnb Price by Host Location (Top 20)'
)

st.altair_chart(chart4)
