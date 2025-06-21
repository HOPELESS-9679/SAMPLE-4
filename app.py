import streamlit as st
import pandas as pd
import folium
import json
from geopy.distance import geodesic
from folium.plugins import LocateControl
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Nursery Locator", layout="wide")
st.title("🌱 Nursery Locator – Tap to View Details")

# 🔹 Load nursery Excel
df = pd.read_excel("NURSARY.xlsx")
required_cols = ['Name', 'Latitude', 'Longitude', 'Capacity', 'PlantsAvailable', 'Contact']
if not all(col in df.columns for col in required_cols):
    st.error("❌ Missing columns: " + ", ".join(required_cols))
    st.stop()

# 🔹 Load Khariar boundary GeoJSON
with open("khariar_boundary.geojson", "r") as f:
    khariar_geojson = json.load(f)

# 🔍 Get user location via browser
st.subheader("📡 Detecting your location...")
loc = streamlit_js_eval(
    js_expressions="navigator.geolocation.getCurrentPosition((pos) => pos.coords)",
    key="get_user_location"
)

if loc and "latitude" in loc and "longitude" in loc:
    user_location = (loc['latitude'], loc['longitude'])
    st.success(f"📍 Your Location: {user_location}")
else:
    user_location = (20.5600, 84.1400)  # fallback
    st.warning("⚠️ Using fallback location (Khariar).")

# 🗺️ Create map
m = folium.Map(location=user_location, zoom_start=10)
LocateControl(auto_start=True).add_to(m)

# Add Khariar boundary
folium.GeoJson(
    khariar_geojson,
    name="Khariar Boundary",
    style_function=lambda x: {
        'fillColor': 'yellow', 'color': 'black', 'weight': 2, 'fillOpacity': 0.1
    }
).add_to(m)

# 🟢 Add nursery markers with tooltips = nursery name
for _, row in df.iterrows():
    popup = f"<b>{row['Name']}</b><br>Capacity: {row['Capacity']}<br>Plants: {row['PlantsAvailable']}<br>Contact: {row['Contact']}"
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=popup,
        tooltip=row['Name'],  # Used for interaction
        icon=folium.Icon(color='green', icon='leaf')
    ).add_to(m)

# 🔵 Add user location marker
folium.Marker(
    location=user_location,
    tooltip="Your Location",
    icon=folium.Icon(color='blue', icon='user')
).add_to(m)

# 🔴 Highlight nearest nursery
df['Distance_km'] = df.apply(lambda row: geodesic(user_location, (row['Latitude'], row['Longitude'])).km, axis=1)
nearest = df.loc[df['Distance_km'].idxmin()]
folium.Marker(
    location=[nearest['Latitude'], nearest['Longitude']],
    popup=f"<b>Nearest:</b> {nearest['Name']}<br>{nearest['Distance_km']:.2f} km away",
    icon=folium.Icon(color='red', icon='star')
).add_to(m)

# Zoom to nearest
m.location = [nearest['Latitude'], nearest['Longitude']]
m.zoom_start = 13

# Show map and track click
st.subheader("🗺️ Click on a nursery to see distance from your location")
map_data = st_folium(m, width=1000, height=600)

# 🟡 Show details on click
if map_data and map_data.get("last_object_clicked_tooltip"):
    clicked_name = map_data["last_object_clicked_tooltip"]
    clicked_row = df[df['Name'] == clicked_name].iloc[0]
    dist = geodesic(user_location, (clicked_row['Latitude'], clicked_row['Longitude'])).km
    st.success(f"📍 {clicked_name}")
    st.markdown(f"""
**Distance from your location:** {dist:.2f} km  
**Capacity:** {clicked_row['Capacity']}  
**Plants Available:** {clicked_row['PlantsAvailable']}  
**Contact:** {clicked_row['Contact']}
    """)
else:
    st.subheader("📍 Nearest Nursery")
    st.markdown(f"""
**Name:** {nearest['Name']}  
**Distance:** {nearest['Distance_km']:.2f} km  
**Capacity:** {nearest['Capacity']}  
**Plants Available:** {nearest['PlantsAvailable']}  
**Contact:** {nearest['Contact']}
    """)
