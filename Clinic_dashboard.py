import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="TN Fertility Clinic Market – Executive Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- DATA LOAD ----------
@st.cache_data
def load_data():
    try:
        # Load your specific CSV file
        df = pd.read_csv("Clinics_Final_Stemmed.csv")
    except FileNotFoundError:
        st.error("File 'Clinics_Final_Stemmed.csv' not found. Please place it in the same directory.")
        return pd.DataFrame() 
    
    # -----------------------------------------------------------
    # DATA CLEANING
    # -----------------------------------------------------------
    # 1. Clean "Independent" duplicates (spaces/capitalization)
    if "Clinic_Type" in df.columns:
        df["Clinic_Type"] = df["Clinic_Type"].astype(str).str.strip().str.title()

    # 2. Rename columns or fill missing values if needed
    if "source" in df.columns:
        df = df.rename(columns={"source": "HQsource"})
        
    if "Brand_name" in df.columns:
        df["Brand_name"] = df["Brand_name"].fillna("Unknown")

    return df

df = load_data()

if df.empty:
    st.stop()

# ---------- THEME TOGGLE ----------
with st.sidebar:
    st.header("Dashboard Settings")
    theme = st.radio("Color Theme", options=["Light", "Dark"], horizontal=True)

if theme == "Light":
    card_color = "#ffffff"
    text_color = "#1c2833"
    plotly_template = "plotly_white"
    color_map_type = {"Chained": "#32b8c6", "Independent": "#1e5f82"}
else:
    card_color = "#0b1020"
    text_color = "#ecf0f1"
    plotly_template = "plotly_dark"
    color_map_type = {"Chained": "#00d1d1", "Independent": "#4da3ff"}

# ---------- CSS STYLING ----------
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    div[data-testid="metric-container"] {{
        background-color: {card_color};
        border: 1px solid rgba(128, 128, 128, 0.1);
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}
    </style>
    """, unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("🏥 Tamil Nadu Fertility Clinic Market")
st.markdown(f"**Executive Dashboard** • For Embryo One")
st.divider()

# ---------- DYNAMIC FILTERS ----------
st.subheader("🔍 Strategic Filters")

col_f1, col_f2, col_f3 = st.columns(3)

# 1. Clinic Type
with col_f1:
    clinic_type_options = sorted(df["Clinic_Type"].dropna().unique())
    selected_types = st.multiselect("Clinic Type", options=clinic_type_options, default=clinic_type_options)

# Intermediate filter
temp_df = df[df["Clinic_Type"].isin(selected_types)]

# 2. District
with col_f2:
    district_options = sorted(temp_df["Mapped_District"].dropna().unique())
    selected_districts = st.multiselect("District", options=district_options, placeholder="All Districts")

if selected_districts:
    temp_df = temp_df[temp_df["Mapped_District"].isin(selected_districts)]

# 3. Brand
with col_f3:
    available_brands = sorted(temp_df[temp_df["Clinic_Type"] == "Chained"]["Brand_name"].dropna().unique())
    if "Chained" in selected_types and len(available_brands) > 0:
        selected_brands = st.multiselect("Brand / Chain Name", options=available_brands, placeholder="All Brands")
    else:
        selected_brands = []

# ---------- APPLYING FINAL FILTERS ----------
filtered = df[df["Clinic_Type"].isin(selected_types)]

if selected_districts:
    filtered = filtered[filtered["Mapped_District"].isin(selected_districts)]

if selected_brands:
    filtered = filtered[filtered["Brand_name"].isin(selected_brands)]

# ---------- METRIC CARDS ----------
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
col_kpi1.metric("Total Clinics", f"{len(filtered)}")
col_kpi2.metric("Districts Covered", f"{filtered['Mapped_District'].nunique()}")
col_kpi3.metric("Chained Units", f"{len(filtered[filtered['Clinic_Type'] == 'Chained'])}")
col_kpi4.metric("Independent Units", f"{len(filtered[filtered['Clinic_Type'] == 'Independent'])}")

st.markdown("---")

# ---------- ROW 1: CHARTS ----------
c1, c2 = st.columns([1, 1])

with c1:
    st.subheader("Market Structure")
    if not filtered.empty:
        fig_pie = px.pie(
            filtered, names="Clinic_Type", 
            color="Clinic_Type",
            color_discrete_map=color_map_type,
            hole=0.5, template=plotly_template
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("No data available.")

with c2:
    st.subheader("Top Districts")
    if not filtered.empty:
        top_dist = filtered["Mapped_District"].value_counts().head(10).reset_index()
        top_dist.columns = ["District", "Count"]
        
        fig_bar = px.bar(
            top_dist, x="Count", y="District", orientation='h',
            text="Count", color="Count", color_continuous_scale="Blues",
            template=plotly_template
        )
        fig_bar.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_bar, use_container_width=True)

# ---------- ROW 2: MAP & BRANDS ----------
c3, c4 = st.columns([1.5, 1])

with c3:
    st.subheader("Geographic Footprint")
    geo_data = filtered.dropna(subset=["Latitude", "Longitude"])
    
    if not geo_data.empty:
        center_lat, center_lon = geo_data["Latitude"].mean(), geo_data["Longitude"].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles="OpenStreetMap")
        
        for _, row in geo_data.iterrows():
            color = "#e74c3c" if row["Clinic_Type"] == "Chained" else "#2980b9"
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=5, color=color, fill=True, fill_opacity=0.8,
                popup=f"<b>{row['Clinic Name']}</b><br>{row['Mapped_District']}"
            ).add_to(m)
            
        st_folium(m, height=400, use_container_width=True)
    else:
        st.info("No GPS coordinates found.")

with c4:
    st.subheader("Top Brands (Chained)")
    chained_data = filtered[filtered["Clinic_Type"] == "Chained"]
    if not chained_data.empty:
        top_brands = chained_data["Brand_name"].value_counts().head(10).reset_index()
        top_brands.columns = ["Brand", "Clinics"]
        
        fig_brand = px.bar(
            top_brands, x="Brand", y="Clinics",
            color="Clinics", color_continuous_scale="Teal",
            template=plotly_template
        )
        st.plotly_chart(fig_brand, use_container_width=True)

st.markdown("---")

# ---------- NEW TABLE: BRAND HEADQUARTERS ----------
st.subheader("🏢 Brand Headquarters")

# Filter for Chained clinics
hq_data = filtered[filtered["Clinic_Type"] == "Chained"]

# 1. FIND THE CORRECT COLUMN FOR ADDRESS
# We look for specific HQ columns first. If not found, we fallback to Google_Full_Address
possible_hq_cols = ['HQ', 'Headquarters', 'HQ Address', 'Google_Full_Address']
valid_hq_col = next((c for c in possible_hq_cols if c in hq_data.columns), None)

if not hq_data.empty and valid_hq_col:
    # Select Brand Name and the identified Address column
    hq_display = hq_data[['Brand_name', valid_hq_col]].copy()
    
    # Rename column for display clarity
    hq_display.rename(columns={valid_hq_col: 'HQ Address / Location'}, inplace=True)
    
    # Deduplicate: Keep one row per Brand Name
    distinct_hq = hq_display.drop_duplicates(subset=['Brand_name']).sort_values('Brand_name')
    
    st.dataframe(distinct_hq, use_container_width=True, hide_index=True)
else:
    if hq_data.empty:
        st.info("No Chained Clinics selected.")
    else:
        st.error(f"Could not find an address column. Checked: {possible_hq_cols}")

st.markdown("---")

# ---------- TABLE 2: DETAILED CLINIC LIST ----------
st.subheader("🏥 Detailed Clinic List")

# ---------------------------------------------------------
# COLUMNS CONFIG
# ---------------------------------------------------------
cols_wanted = ["Clinic Name", "Google_Full_Address", "Email", "Mapped_District"]

# 1. Verify which columns actually exist in the dataframe
valid_cols = [c for c in cols_wanted if c in filtered.columns]

# 2. Check if the address column is missing (Debug Helper)
if "Google_Full_Address" not in filtered.columns:
    st.error("⚠️ Column 'Google_Full_Address' not found in CSV. Please check your CSV header.")
    with st.expander("Show all available columns (Debug)"):
        st.write(list(filtered.columns))

# 3. Display the dataframe
st.dataframe(
    filtered[valid_cols].sort_values("Mapped_District"),
    use_container_width=True,
    hide_index=True
)