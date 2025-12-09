import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

# ---------- DATA LOAD ----------
@st.cache_data
def load_data():
    df = pd.read_csv("Clinics_Final_Stemmed.csv")
    return df

df = load_data()

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="TN Fertility Clinic Market – Executive Dashboard",
    layout="wide"
)

# ---------- THEME TOGGLE (for charts/cards) ----------
theme_col1, theme_col2 = st.columns([1, 3])
with theme_col1:
    theme = st.radio(
        "Theme (charts/cards)",
        options=["Light", "Dark"],
        horizontal=True
    )

if theme == "Light":
    card_color = "#ffffff"
    text_color = "#1c2833"
    plotly_template = "plotly_white"
    color_map_type = {
        "Chained": "#32b8c6",
        "Independent": "#1e5f82"
    }
else:
    card_color = "#0b1020"
    text_color = "#ecf0f1"
    plotly_template = "plotly_dark"
    color_map_type = {
        "Chained": "#00d1d1",
        "Independent": "#4da3ff"
    }

# ---------- GLOBAL STYLES (FONT + CARD SHAPE) ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    h1, h2, h3, h4 {
        font-weight: 600;
    }

    div[data-testid="metric-container"] {
        border-radius: 12px;
        padding: 12px 16px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.04);
    }

    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Tamil Nadu Fertility Clinic Market – Executive Dashboard")
st.caption("Clinics_Final_Stemmed.csv • Confidential • For CEO / Owners / HR")

st.markdown("---")

# ---------- STRATEGIC FILTERS ----------
st.subheader("Strategic Filters")
col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    clinic_type_filter = st.multiselect(
        "Clinic Type",
        options=sorted(df["Clinic_Type"].unique()),
        default=sorted(df["Clinic_Type"].unique())
    )

with col_f2:
    district_filter = st.multiselect(
        "Mapped District",
        options=sorted(df["Mapped_District"].unique()),
        default=None,
        placeholder="All districts"
    )

with col_f3:
    brand_filter = st.multiselect(
        "Brand / Chain Name",
        options=sorted(df["Brand_name"].unique()),
        default=None,
        placeholder="All brands"
    )

filtered = df[df["Clinic_Type"].isin(clinic_type_filter)]

if district_filter:
    filtered = filtered[filtered["Mapped_District"].isin(district_filter)]

if brand_filter:
    filtered = filtered[filtered["Brand_name"].isin(brand_filter)]

# ---------- FILTERED METRICS (RESPOND TO SELECTIONS) ----------
filtered_total = len(filtered)
filtered_districts = filtered["Mapped_District"].nunique()
filtered_chains = (filtered["Clinic_Type"] == "Chained").sum()
filtered_independent = (filtered["Clinic_Type"] == "Independent").sum()

# ---------- TOP KPI CARDS (FILTER-AWARE) ----------
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    st.metric("Total Clinics (filtered)", f"{filtered_total}")

with kpi_col2:
    st.metric("Districts (filtered)", f"{filtered_districts}")

with kpi_col3:
    st.metric("Chained Clinics (filtered)", f"{filtered_chains}")

with kpi_col4:
    st.metric("Independent Clinics (filtered)", f"{filtered_independent}")

st.markdown("")

# ---------- ROW 1: MARKET STRUCTURE & DISTRICTS ----------
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("Market Structure – Chained vs Independent")
    structure = (
        filtered.groupby("Clinic_Type")["Clinic Name"]
        .count()
        .reset_index()
        .rename(columns={"Clinic Name": "Count"})
    )
    fig_pie = px.pie(
        structure,
        names="Clinic_Type",
        values="Count",
        color="Clinic_Type",
        color_discrete_map=color_map_type,
        hole=0.4,
        template=plotly_template
    )
    fig_pie.update_layout(
        showlegend=True,
        legend_title_text="Clinic Type",
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor=card_color,
        plot_bgcolor=card_color,
        font_color=text_color
    )
    st.plotly_chart(fig_pie, width="stretch")

with row1_col2:
    st.subheader("Top Districts by Clinic Count (High to Low)")
    top_districts = (
        filtered.groupby("Mapped_District")["Clinic Name"]
        .count()
        .reset_index()
        .rename(columns={"Clinic Name": "Clinics"})
        .sort_values("Clinics", ascending=True)
    )
    fig_bar_dist = px.bar(
        top_districts,
        x="Clinics",
        y="Mapped_District",
        orientation="h",
        color="Clinics",
        color_continuous_scale="Blues",
        template=plotly_template
    )
    fig_bar_dist.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor=card_color,
        plot_bgcolor=card_color,
        font_color=text_color
    )
    st.plotly_chart(fig_bar_dist, width="stretch")

# ---------- ROW 2: TOP BRANDS & MAP ----------
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("Top Clinic Networks (Brands)")
    chains_only = filtered[filtered["Clinic_Type"] == "Chained"]
    top_brands = (
        chains_only.groupby("Brand_name")["Clinic Name"]
        .count()
        .reset_index()
        .rename(columns={"Clinic Name": "Clinics"})
        .sort_values("Clinics", ascending=False)
    )
    if not top_brands.empty:
        fig_bar_brand = px.bar(
            top_brands,
            x="Brand_name",
            y="Clinics",
            text="Clinics",
            color="Clinics",
            color_continuous_scale="Oranges",
            template=plotly_template
        )
        fig_bar_brand.update_traces(textposition="outside")
        fig_bar_brand.update_layout(
            xaxis_title="Brand / Chain",
            yaxis_title="Number of Clinics",
            coloraxis_showscale=False,
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor=card_color,
            plot_bgcolor=card_color,
            font_color=text_color
        )
        st.plotly_chart(fig_bar_brand, width="stretch")
    else:
        st.info("No chained clinics in current filter selection.")

with row2_col2:
    st.subheader("Geographic Footprint – Clinic Map")

    geo = filtered.dropna(subset=["Latitude", "Longitude"])

    if not geo.empty:
        center_lat = geo["Latitude"].mean()
        center_lon = geo["Longitude"].mean()

        m = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles="OpenStreetMap")

        for _, row in geo.iterrows():
            popup_text = f"{row['Clinic Name']}<br>{row['Mapped_District']}<br>{row['Clinic_Type']} – {row['Brand_name']}"
            color = "#e74c3c" if row["Clinic_Type"] == "Chained" else "#2980b9"
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=4,
                color=color,
                fill=True,
                fill_opacity=0.9,
                popup=popup_text,
            ).add_to(m)

        st_folium(m, width=900, height=450)
    else:
        st.info("No geocoded clinics available for the current filter selection.")

# ---------- CLINIC NAME SELECTOR FOR DETAIL TABLE ----------
st.subheader("Clinic Detail (Filtered View)")

# Add clinic name selector
clinic_names = sorted(filtered["Clinic Name"].unique())
selected_clinic = st.selectbox(
    "Select a specific clinic (optional)",
    options=["All clinics"] + list(clinic_names),
    index=0,
    placeholder="Choose a clinic to focus on"
)

# Filter by selected clinic
if selected_clinic != "All clinics":
    detail_filtered = filtered[filtered["Clinic Name"] == selected_clinic]
else:
    detail_filtered = filtered

detail_cols = [
    "Clinic Name",
    "Mapped_District",
    "Clinic_Type",
    "Brand_name",
    "Extracted_Pincode",
    "Email"
]
st.dataframe(
    detail_filtered[detail_cols].sort_values("Mapped_District"),
    width="stretch",
    hide_index=True
)
