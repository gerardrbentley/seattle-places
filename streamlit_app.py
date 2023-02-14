from typing import List, Set, Union

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
from streamlit_elements import elements, mui, html


from interactors import Place, get_data

get_data = st.cache_data()(get_data)
SELECTED_LOCATION = "selected_location"
CENTER_START = [47.6142, -122.3211]
ZOOM_START = 16

st.set_page_config(page_title="Seattle Places", page_icon="🍻", layout="wide", initial_sidebar_state="collapsed")

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


if st.sidebar.checkbox("Categories", True):
    selected_categories = st.sidebar.multiselect("Categories", categories, categories)
else:
    selected_categories = set()
if st.sidebar.checkbox("Tags"):
    selected_tags = st.sidebar.multiselect("Tags", tags, None)
else:
    selected_tags = set()
if st.sidebar.checkbox("Price Range"):
    min_price, max_price = st.sidebar.slider(
        "Cost Per Person Range", 0, 50, value=[0, 50], step=5
    )
else:
    min_price, max_price = None, None

if st.sidebar.checkbox("Min Rating"):
    min_rating = st.sidebar.number_input(
        "Min Rating (*)", 0.0, 5.0, value=4.0, step=0.5
    )
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


warning_block = st.empty()

left_col, right_col = st.columns(2)

with st.expander("Filtered Locations: ", False):
    st.dataframe(filtered_data)
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
    warning_block.warning(
        """\
Select a location on the map to view details 📍

Filter with the sidebar menu on the left

Scroll down to view a table of all locations 🗺
"""
    )
    st.stop()

if (
    st.session_state.get(SELECTED_LOCATION)
    != map_selection["last_object_clicked_tooltip"]
):
    st.session_state[SELECTED_LOCATION] = map_selection["last_object_clicked_tooltip"]
    st.experimental_rerun()

lookup = data[st.session_state[SELECTED_LOCATION]]

with right_col:
    with elements("display_card"):
        with mui.Card:
            name_parts = lookup.name.split()
            display_name = lookup.name[0].title()
            if len(name_parts) > 1:
                display_name = display_name + name_parts[1][0].title()
            mui.CardHeader(
                title=lookup.name,
                subheader=lookup.category,
                avatar=mui.Avatar(
                    display_name,
                    sx={
                        "bgcolor": color_map.get(lookup.category, "red"),
                        "color": "white",
                    },
                ),
            )

            with mui.CardContent(sx={"flex": 1}):
                for line in lookup.description.split("\n"):
                    if line.strip() != "":
                        mui.Typography(line)
                    else:
                        html.br()
                html.br()
                for tag in lookup.tags.split(","):
                    if tag != "":
                        mui.Chip(label=tag)

                html.br()
                html.br()
                mui.Typography(
                    "Cost Per Person: $" + str(lookup.cost_per_person), variant="h6"
                )
                mui.Rating(value=lookup.rating, precision=0.1, readOnly=True)
            with mui.CardActions(disableSpacing=True):
                mui.IconButton(
                    mui.icon.Launch,
                    href=lookup.homepage,
                    target="_blank",
                    rel="noreferrer",
                )
                mui.IconButton(
                    mui.icon.Directions,
                    href=lookup.maps_url,
                    target="_blank",
                    rel="noreferrer",
                )
