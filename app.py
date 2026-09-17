"""
Step 4 (v2): Main Streamlit app with improved UI/UX.
Restaurant Location Opportunity Checker for Greater Noida.

WHAT'S NEW in this version:
1. A 500m radius circle is drawn around the clicked point, so it's
   visually obvious what area the score is based on.
2. A colored marker appears at the clicked point itself (green/orange/
   red/gray depending on verdict) -- feedback right on the map, not
   just in the sidebar.
3. Cleaner sidebar: icons per verdict, and an actual table of nearby
   competitors (name, category, distance) instead of a plain sentence.

HOW CLICK PERSISTENCE WORKS:
Streamlit reruns the whole script top-to-bottom on every interaction.
To "remember" the last click (so we can draw its circle/marker), we
store it in st.session_state. When a NEW click comes in via st_folium,
we save it and trigger one st.rerun() so the map redraws immediately
with the new circle/marker -- otherwise it would lag one click behind.
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
from feature_engineering import load_restaurant_data, get_verdict_and_reason, get_nearby_places

# ---------- Page setup ----------
st.set_page_config(
    page_title="Restaurant Location Checker - Greater Noida",
    page_icon="🍽️",
    layout="wide"
)

st.markdown("""
    <style>
    .verdict-good { color: #2ecc71; font-weight: 700; font-size: 1.5rem; }
    .verdict-moderate { color: #f39c12; font-weight: 700; font-size: 1.5rem; }
    .verdict-risky { color: #e74c3c; font-weight: 700; font-size: 1.5rem; }
    .verdict-nodata { color: #95a5a6; font-weight: 700; font-size: 1.5rem; }
    </style>
""", unsafe_allow_html=True)

st.title("🍽️ Restaurant Location Opportunity Checker")
st.caption("Click anywhere on the map within Greater Noida to check the opportunity score for opening a restaurant there.")

# ---------- Verdict styling lookup ----------
VERDICT_STYLE = {
    "Good Opportunity":       {"class": "verdict-good",     "icon": "✅", "color": "green"},
    "Moderate Opportunity":   {"class": "verdict-moderate", "icon": "⚠️", "color": "orange"},
    "Risky - Saturated Area": {"class": "verdict-risky",    "icon": "🚫", "color": "red"},
    "Insufficient Data":      {"class": "verdict-nodata",   "icon": "❔", "color": "gray"},
}

# ---------- Load data (cached) ----------
@st.cache_data
def get_data():
    return load_restaurant_data()

df = get_data()

# ---------- Session state: remember the last click across reruns ----------
if "clicked_lat" not in st.session_state:
    st.session_state.clicked_lat = None
    st.session_state.clicked_lon = None

# ---------- Layout ----------
col_map, col_result = st.columns([2, 1])

with col_map:
    m = folium.Map(location=[28.4744, 77.5040], zoom_start=13, tiles="CartoDB dark_matter")

    # Plot existing restaurants
    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=3,
            color="#3498db",
            fill=True,
            fill_opacity=0.6,
            popup=f"{row['name']} ({row['category']})"
        ).add_to(m)

    # If we have a stored click, draw the radius circle + verdict marker
    if st.session_state.clicked_lat is not None:
        lat, lon = st.session_state.clicked_lat, st.session_state.clicked_lon
        result = get_verdict_and_reason(lat, lon, df)
        style = VERDICT_STYLE[result["verdict"]]

        # 500m radius circle
        folium.Circle(
            location=[lat, lon],
            radius=500,
            color=style["color"],
            fill=True,
            fill_opacity=0.08,
            weight=2
        ).add_to(m)

        # Verdict marker at the exact clicked point
        folium.Marker(
            location=[lat, lon],
            icon=folium.Icon(color=style["color"], icon="cutlery", prefix="fa"),
            popup=f"{result['verdict']} (Score: {result['score']})"
        ).add_to(m)

    map_data = st_folium(m, width=800, height=600, key="main_map")

    # Detect a NEW click and store it, then rerun so the map redraws
    # immediately with the circle/marker for this click.
    if map_data and map_data.get("last_clicked"):
        new_lat = map_data["last_clicked"]["lat"]
        new_lon = map_data["last_clicked"]["lng"]
        if (new_lat, new_lon) != (st.session_state.clicked_lat, st.session_state.clicked_lon):
            st.session_state.clicked_lat = new_lat
            st.session_state.clicked_lon = new_lon
            st.rerun()

with col_result:
    st.subheader("Result")

    if st.session_state.clicked_lat is not None:
        lat, lon = st.session_state.clicked_lat, st.session_state.clicked_lon
        result = get_verdict_and_reason(lat, lon, df)
        style = VERDICT_STYLE[result["verdict"]]

        st.write(f"**Location:** {lat:.5f}, {lon:.5f}")

        st.markdown(
            f'<p class="{style["class"]}">{style["icon"]} {result["verdict"]}</p>',
            unsafe_allow_html=True
        )

        if result["score"] is not None:
            st.metric("Opportunity Score", f"{result['score']} / 100")

        st.write(result["reason"])

        # Nearby competitors table
        nearby = get_nearby_places(lat, lon, df)
        if len(nearby) > 0:
            st.markdown("**Nearby competitors:**")
            display_df = nearby[["name", "category", "distance_m"]].copy()
            display_df["distance_m"] = display_df["distance_m"].round(0).astype(int)
            display_df = display_df.rename(columns={
                "name": "Name", "category": "Category", "distance_m": "Distance (m)"
            }).sort_values("Distance (m)")
            st.dataframe(display_df, hide_index=True, use_container_width=True)

        if st.button("Clear selection"):
            st.session_state.clicked_lat = None
            st.session_state.clicked_lon = None
            st.rerun()
    else:
        st.info("👆 Click a point on the map to see the opportunity score for that location.")

# ---------- Footer / limitations note ----------
st.divider()
with st.expander("About this tool & limitations"):
    st.markdown("""
    **How the score works:** based on distance-weighted nearby restaurant
    competitor density (within 500m) and category diversity in our dataset.
    Closer competitors count more heavily than ones near the edge of the radius.

    **Known limitations:**
    - Dataset covers 108 restaurants pulled from Foursquare's Places API
      for Greater Noida -- not exhaustive, so sparse areas may show
      "Insufficient Data" even if they're genuinely fine locations.
    - This tool does not use customer ratings/reviews (both Google and
      Foursquare gate that data behind paid tiers) -- the score reflects
      market saturation only, not customer sentiment.
    - Always verify with on-ground research before making real decisions.
    """)