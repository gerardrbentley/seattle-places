from typing import List, Set, Union

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from interactors import Place, get_data

get_data = st.cache_data()(get_data)
SELECTED_LOCATION = "selected_location"
CENTER_START = [47.6142, -122.3211]
ZOOM_START = 16

st.set_page_config("Seattle Places", layout="wide")

st.header("Seattle Places")

data, categories, tags = get_data()
if not len(data):
    st.exception("Error Getting Data")
    st.stop()


@st.cache_data
def filter_data(
    raw_data: List[Place],
    selected_categories: Set[str],
    selected_tags: Set[str],
    min_price: Union[float, None],
    max_price: Union[float, None],
    min_rating: Union[float, None],
) -> pd.DataFrame:
    good_data = []
    for row in raw_data:
        if row.category not in selected_categories:
            continue
        if len(selected_tags) and not selected_tags.intersection(
            set(row.tags.split(","))
        ):
            continue
        if min_price is not None and row.cost_per_person < min_price:
            continue
        if max_price is not None and row.cost_per_person > max_price:
            continue
        if min_rating is not None and row.rating < min_rating:
            continue
        good_data.append(row)
    df = pd.DataFrame(good_data)
    if len(df):
        return df.drop("record_id", axis=1)
    else:
        return df


with st.expander("Filter Locations: ", False):
    if st.checkbox("Categories", True):
        selected_categories = st.multiselect("Categories", categories, categories)
    else:
        selected_categories = set()
    if st.checkbox("Tags"):
        selected_tags = st.multiselect("Tags", tags, None)
    else:
        selected_tags = set()
    if st.checkbox("Min Price"):
        min_price = st.number_input("Min Price ($)", 0, value=10, step=5)
    else:
        min_price = None
    if st.checkbox("Max Price"):
        max_price = st.number_input("Max Price ($)", 0, value=30, step=5)
    else:
        max_price = None

    if st.checkbox("Min Rating"):
        min_rating = st.number_input("Min Rating (*)", 0.0, 5.0, value=4.0, step=0.5)
    else:
        min_rating = None

    filtered_data = filter_data(
        list(data.values()),
        set(selected_categories),
        set(selected_tags),
        min_price,
        max_price,
        min_rating,
    )
    st.dataframe(filtered_data)


left_col, right_col = st.columns(2)

fg = folium.FeatureGroup(name="Seattle Locations")
m = folium.Map(location=CENTER_START, zoom_start=ZOOM_START)

# https://fontawesome.com/v4/icons/
icon_map = {
    "Restaurant": "cutlery",
    "Bar": "glass",
    "Nature": "tree",
    "Coffee Shop": "coffee",
    "Shopping": "shopping-bag",
    "Learning": "book",
}

# [‘red’, ‘blue’, ‘green’, ‘purple’, ‘orange’, ‘darkred’,
# ’lightred’, ‘beige’, ‘darkblue’, ‘darkgreen’, ‘cadetblue’, ‘darkpurple’, ‘white’, ‘pink’, ‘lightblue’, ‘lightgreen’, ‘gray’, ‘black’, ‘lightgray’]
color_map = {
    "Restaurant": "blue",
    "Bar": "red",
    "Nature": "darkgreen",
    "Coffee Shop": "beige",
    "Shopping": "purple",
    "Learning": "gray",
}

for row in filtered_data.itertuples():
    color = color_map.get(row.category)
    if row.name == st.session_state.get(SELECTED_LOCATION):
        color = "black"
    fg.add_child(
        folium.Marker(
            [row.lat, row.lon],
            popup=[row.name, row.category],
            tooltip=row.name,
            icon=folium.Icon(color=color, icon=icon_map.get(row.category), prefix="fa"),
        )
    )


with left_col:
    map_selection = st_folium(
        m,
        width=725,
        returned_objects=[
            "last_object_clicked",
            "last_object_clicked_tooltip",
            "last_clicked",
        ],
        feature_group_to_add=fg,
    )


if (
    map_selection.get("last_object_clicked_tooltip") is None
    and st.session_state.get(SELECTED_LOCATION) is None
):
    st.warning("Select a location to view details")
    st.stop()

if (
    st.session_state.get(SELECTED_LOCATION)
    != map_selection["last_object_clicked_tooltip"]
):
    st.session_state[SELECTED_LOCATION] = map_selection["last_object_clicked_tooltip"]
    st.experimental_rerun()

lookup = data[st.session_state[SELECTED_LOCATION]]

with right_col:
    st.header(lookup.name)
    st.write("## Category: " + lookup.category)
    st.write("## Tags: ", lookup.tags)
    st.write("## Description:\n\n" + lookup.description.replace("\n", "\n\n"))

    st.write("## Cost Per Person: " + f"$`{lookup.cost_per_person:.2f}`")
    st.write(f"## Rating: `{lookup.rating}`")
    st.write(f"## Homepage: [{lookup.homepage}]()")
    st.write(f"## Maps URL: [{lookup.maps_url}]()")
    st.write(f"## Location: `{lookup.lat},{lookup.lon}`")
