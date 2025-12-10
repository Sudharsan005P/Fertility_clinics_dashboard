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
        df = pd.read_csv("Clinics_Final_Stemmed.csv")
    except FileNotFoundError:
        st.error("File 'Clinics_Final_Stemmed.csv' not found. Please place it in the same directory.")
        return pd.DataFrame() 
    
    # --- DATA CLEANING ---
    # 1. Standardize Clinic Type (Fix "Another Independent" issue)
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

# ---------- FILTERS ----------
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
    available_brands = sorted(temp_df[temp_df["Clinic_Type"] == "Chained"]["Brand_name"].dropna().unique())
    selected_brands = st.multiselect("Brand", options=available_brands, placeholder="All Brands") if "Chained" in selected_types else []

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
        m = folium.Map(location=tn_center, zoom_start=7, tiles=None) # tiles=None is crucial

        # Google Maps Layer
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
    chained = filtered[filtered["Clinic_Type"] == "Chained"]
    if not chained.empty:
        top_brands = chained["Brand_name"].value_counts().head(10).reset_index()
        fig = px.bar(top_brands, x="Brand_name", y="count", template=plotly_template)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ---------- TABLE 1: BRAND HEADQUARTERS (FIXED) ----------
st.subheader("🏢 Brand Headquarters")

# 1. Get the list of brands currently visible in the dashboard (from filters)
visible_brands = filtered[filtered["Clinic_Type"] == "Chained"]["Brand_name"].unique()

# 2. Look up the HQ address from the MASTER dataset (df)
#    This ensures we find the HQ address even if the specific rows in 'filtered' (e.g. filtered by district) don't have it.
if "HQ" in df.columns:
    # Get all Chained brands from the full file
    master_hq = df[df["Clinic_Type"] == "Chained"]
    
    # Create a reference table of Brand -> HQ
    # dropna() removes rows with no HQ address
    # drop_duplicates() ensures we only have ONE row per brand
    hq_reference = master_hq[["Brand_name", "HQ"]].dropna().drop_duplicates(subset=["Brand_name"])
    
    # 3. Filter this reference table to only show brands the user has selected/filtered
    final_hq_table = hq_reference[hq_reference["Brand_name"].isin(visible_brands)].sort_values("Brand_name")
    
    st.dataframe(final_hq_table, use_container_width=True, hide_index=True)

else:
    st.error("⚠️ Column 'HQ' not found. Please ensure your CSV has a column named 'HQ' for this table.")

st.markdown("---")

# ---------- TABLE 2: DETAILED LIST (With Google_Full_Address) ----------
st.subheader("🏥 Detailed Clinic List")

cols_wanted = ["Clinic Name", "Google_Full_Address", "Email", "Mapped_District"]
valid_cols = [c for c in cols_wanted if c in filtered.columns]

st.dataframe(
    filtered[valid_cols].sort_values("Mapped_District"),
    use_container_width=True,
    hide_index=True
)