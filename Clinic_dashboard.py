import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="TN Fertility Clinic Market – Executive Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- DATA LOAD (PUBLIC LINK METHOD) ----------
@st.cache_data(ttl=10)
def load_data():
    # -------------------------------------------------------------
    # 1. PASTE YOUR GOOGLE SHEET LINK BELOW
    # -------------------------------------------------------------
    sheet_url = "https://docs.google.com/spreadsheets/d/1Yb07Bkkxj6PXCLGe2_2Wn7IxHuPxHiKpXWxSENFW8_k/edit?usp=sharing" 
    
    # -------------------------------------------------------------
    # AUTOMATIC URL CONVERTER
    # -------------------------------------------------------------
    try:
        if "docs.google.com" in sheet_url:
            csv_url = sheet_url.replace("/edit?usp=sharing", "/export?format=csv")
            csv_url = csv_url.replace("/edit", "/export?format=csv")
        else:
            csv_url = sheet_url

        df = pd.read_csv(csv_url)
        
    except Exception as e:
        st.error(f"⚠️ Error loading data. Please ensure the Google Sheet is set to 'Anyone with the link'.\nError details: {e}")
        return pd.DataFrame() 
    
    # --- DATA CLEANING ---
    # 1. Standardize Clinic Type
    if "Clinic_Type" in df.columns:
        df["Clinic_Type"] = df["Clinic_Type"].astype(str).str.strip().str.title()
    
    # 2. Rename columns / Fill Missing Values
    if "source" in df.columns:
        df = df.rename(columns={"source": "HQsource"})
    if "Brand_name" in df.columns:
        df["Brand_name"] = df["Brand_name"].fillna("Unknown")
    if "Email" in df.columns:
        df["Email"] = df["Email"].fillna("Not Available")

    return df

df = load_data()

if df.empty:
    st.stop()

# ---------- THEME ----------
with st.sidebar:
    st.header("Dashboard Settings")
    theme = st.radio("Color Theme", options=["Light", "Dark"], horizontal=True)

if theme == "Light":
    card_color = "#ffffff"
    text_color = "#1c2833"
    plotly_template = "plotly_white"
else:
    card_color = "#0b1020"
    text_color = "#ecf0f1"
    plotly_template = "plotly_dark"

# ---------- STYLING ----------
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    div[data-testid="metric-container"] {{
        background-color: {card_color};
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}
    </style>
    """, unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("🏥 Tamil Nadu Fertility Clinic Market")
st.divider()

# ---------- FILTERS (TOP) ----------
col_f1, col_f2, col_f3 = st.columns(3)

# Filter 1: Type
with col_f1:
    clinic_type_options = sorted(df["Clinic_Type"].dropna().unique())
    selected_types = st.multiselect("Clinic Type", options=clinic_type_options, default=clinic_type_options)
    temp_df = df[df["Clinic_Type"].isin(selected_types)]

# Filter 2: District
with col_f2:
    district_options = sorted(temp_df["Mapped_District"].dropna().unique())
    selected_districts = st.multiselect("District", options=district_options, placeholder="All Districts")
    if selected_districts:
        temp_df = temp_df[temp_df["Mapped_District"].isin(selected_districts)]

# Filter 3: Brand
with col_f3:
    available_brands = sorted(temp_df["Brand_name"].dropna().unique())
    selected_brands = st.multiselect("Brand", options=available_brands, placeholder="All Brands")

# Apply Filters
filtered = df[df["Clinic_Type"].isin(selected_types)]
if selected_districts: filtered = filtered[filtered["Mapped_District"].isin(selected_districts)]
if selected_brands: filtered = filtered[filtered["Brand_name"].isin(selected_brands)]

# ---------- METRICS ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Clinics", len(filtered))
c2.metric("Districts", filtered['Mapped_District'].nunique())
c3.metric("Chained", len(filtered[filtered['Clinic_Type'] == 'Chained']))
c4.metric("Independent", len(filtered[filtered['Clinic_Type'] == 'Independent']))

st.markdown("---")

# ---------- CHARTS ----------
col1, col2 = st.columns(2)
with col1:
    if not filtered.empty:
        fig = px.pie(filtered, names="Clinic_Type", hole=0.5, template=plotly_template)
        st.plotly_chart(fig, use_container_width=True)
with col2:
    if not filtered.empty:
        top_dist = filtered["Mapped_District"].value_counts().head(10).reset_index()
        fig = px.bar(top_dist, x="count", y="Mapped_District", orientation='h', template=plotly_template)
        fig.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

# ---------- MAP (Google Maps + TN Filter) ----------
col_map, col_brand = st.columns([1.5, 1])

with col_map:
    st.subheader("Geographic Footprint (Google Maps)")
    
    # Filter specifically for Tamil Nadu Lat/Lon Box
    mask_tn = (
        (filtered["Latitude"] >= 8.0) & (filtered["Latitude"] <= 14.0) &
        (filtered["Longitude"] >= 76.0) & (filtered["Longitude"] <= 81.0)
    )
    geo_data = filtered[mask_tn].copy()

    if not geo_data.empty:
        tn_center = [11.1271, 78.6569]
        m = folium.Map(location=tn_center, zoom_start=7, tiles=None)

        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Maps',
            overlay=False,
            control=True
        ).add_to(m)

        for _, row in geo_data.iterrows():
            color = "#e74c3c" if row["Clinic_Type"] == "Chained" else "#2980b9"
            
            popup_html = f"""
            <div style="font-family:sans-serif; width:200px">
                <b>{row['Clinic Name']}</b><br>
                <span style="color:gray">{row['Mapped_District']}</span><br>
                📧 {row['Email']}
            </div>
            """
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=6, color=color, fill=True, fill_opacity=0.8,
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(m)
            
        st_folium(m, height=400, use_container_width=True)
    else:
        st.info("No clinics found within Tamil Nadu bounds.")

with col_brand:
    st.subheader("Top Brands")
    if not filtered.empty:
        top_brands = filtered["Brand_name"].value_counts().head(10).reset_index()
        fig = px.bar(top_brands, x="Brand_name", y="count", template=plotly_template)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ---------- TABLE 1: BRAND HEADQUARTERS ----------
st.subheader("🏢 Brand Headquarters")

visible_brands = filtered["Brand_name"].unique()

if "HQ" in df.columns:
    hq_reference = df[["Brand_name", "HQ"]].dropna().drop_duplicates(subset=["Brand_name"])
    final_hq_table = hq_reference[hq_reference["Brand_name"].isin(visible_brands)].sort_values("Brand_name")
    st.dataframe(final_hq_table, use_container_width=True, hide_index=True)
else:
    st.warning("⚠️ Column 'HQ' not found. Check your CSV headers.")

st.markdown("---")

# ---------- TABLE 2: DETAILED LIST WITH SEARCH (NEW!) ----------
st.subheader("🏥 Detailed Clinic List")

# 1. Search Bar
search_query = st.text_input("🔍 Search Clinic, District, or Brand", placeholder="Type to search... (e.g., 'Apollo' or 'Chennai')")

cols_wanted = ["Clinic Name", "Google_Full_Address", "Email", "Mapped_District", "Brand_name"]
valid_cols = [c for c in cols_wanted if c in filtered.columns]

# 2. Filter Logic based on search
if search_query:
    # Check if the search query exists in ANY of the visible columns
    # We convert everything to string (.astype(str)) and lowercase (.str.lower()) for easy matching
    mask = filtered[valid_cols].apply(
        lambda row: row.astype(str).str.lower().str.contains(search_query.lower()).any(), axis=1
    )
    table_to_show = filtered[mask]
else:
    table_to_show = filtered

# 3. Show Table
st.dataframe(
    table_to_show[valid_cols].sort_values("Mapped_District"),
    use_container_width=True,
    hide_index=True
)