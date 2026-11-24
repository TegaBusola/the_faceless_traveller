
from pathlib import Path
import re

import pandas as pd
import plotly.express as px
import pycountry
import streamlit as st
from PIL import Image, ImageOps


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="The Faceless Traveller",
    page_icon="🌍",
    layout="wide",
)


# ============================================================
# 2. COLOUR PALETTE
# ============================================================

BG = "#08312A"
TEXT = "#F6F5F0"
MUTED = "#B8C9BE"
SAGE = "#8FAF9A"
TERRACOTTA = "#C98768"
MOSS = "#354A46"
GOLD = "#D6B978"
BORDER = "#42645A"


# ============================================================
# 3. CUSTOM CSS
# ============================================================

st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {BG};
            color: {TEXT};
        }}

        [data-testid="stSidebar"] {{
            background-color: {MOSS};
        }}

        h1, h2, h3, h4 {{
            font-family: Georgia, serif !important;
            color: {TEXT} !important;
        }}

        p, label, span, div {{
            color: inherit;
        }}

        .main .block-container {{
            padding-top: 3rem;
            padding-bottom: 4rem;
            max-width: 1500px;
        }}

        .intro-title {{
            font-family: Georgia, serif;
            font-size: 3.1rem;
            color: {TEXT};
            margin-bottom: 0.35rem;
        }}

        .intro-subtitle {{
            font-size: 1.05rem;
            color: {MUTED};
            margin-bottom: 2.5rem;
        }}

        .stat-label {{
            color: {MUTED};
            font-size: 0.78rem;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            min-height: 2.3rem;
        }}

        .stat-value {{
            color: {TEXT};
            font-family: Georgia, serif;
            font-size: 1.65rem;
            font-weight: 600;
            margin-top: 0.3rem;
        }}

        .stat-divider {{
            border-right: 1px solid {BORDER};
            min-height: 75px;
        }}

        .section-heading {{
            font-family: Georgia, serif;
            font-size: 1.65rem;
            color: {TEXT};
            margin-top: 2rem;
            margin-bottom: 0.3rem;
        }}

        .section-caption {{
            color: {MUTED};
            font-size: 0.88rem;
            margin-bottom: 1rem;
        }}

        .wonder-name {{
            font-family: Georgia, serif;
            color: {TEXT};
            font-size: 0.9rem;
        }}

        .wonder-status {{
            color: {MUTED};
            font-size: 0.72rem;
        }}

        .story-card {{
            border-top: 1px solid {BORDER};
            padding-top: 1rem;
            margin-top: 0.5rem;
        }}

        .story-title {{
            font-family: Georgia, serif;
            font-size: 1.2rem;
            color: {TEXT};
        }}

        .story-caption {{
            font-size: 0.85rem;
            color: {MUTED};
        }}

        div[data-testid="stProgressBar"] > div > div {{
            background-color: {SAGE};
        }}

        hr {{
            border-color: {BORDER};
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 4. GOOGLE SHEETS DATA SOURCE
# ============================================================

SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vSUO8OtcwC1KXueexdiRXl4zonQUBset3XQ5DVhBV7RSOHiKq96xjSLFH1x8hHHUeZz6EIMqiLm6gqU/pub?gid=970747426&single=true&output=csv"
)

PROJECT_DIR = Path(__file__).parent
WONDER_IMAGE_DIR = PROJECT_DIR / "wonders"


@st.cache_data(ttl=300)
def load_data():
    """Load and clean travel data from the published Google Sheet."""

    df = pd.read_csv(SHEET_CSV_URL)

    # Standardise column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # Clean text columns
    text_columns = [
        "country",
        "city",
        "status",
        "visit_type",
        "continent",
        "wonder",
        "blog_titles",
        "blog_url",
    ]

    for column in text_columns:
        if column in df.columns:
            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
                .replace("", pd.NA)
            )

    # Standardise country names
    country_corrections = {
        "America": "United States",
        "USA": "United States",
        "US": "United States",
        "México": "Mexico",
        "Montengero": "Montenegro",
        "Mynamar": "Myanmar",
        "Mauritiaus": "Mauritius",
        "Soa Tome & Principe": "Sao Tome and Principe",
        "Azerbejan": "Azerbaijan",
        "Belieze": "Belize",
        "Trinidad & Tobago": "Trinidad and Tobago",
        "St Lucia": "Saint Lucia",
        "Republic of Ireland": "Ireland",
    }

    df["country"] = df["country"].replace(country_corrections)

    # Standardise city and wonder names
    df["city"] = df["city"].replace({
        "Rio De Janerio": "Rio de Janeiro",
    })

    df["wonder"] = df["wonder"].replace({
        "Christ the Reedemer": "Christ the Redeemer",
    })

    # Standardise status and visit type
    df["status"] = df["status"].str.strip().str.lower()
    df["visit_type"] = df["visit_type"].str.strip().str.title()

    # Convert visit counts to numeric
    df["no_of_visits"] = pd.to_numeric(
        df["no_of_visits"],
        errors="coerce",
    ).fillna(0)

    return df


try:
    travel_df = load_data()

except Exception as error:
    st.error(
        "I couldn't load the travel data from Google Sheets. "
        "Please check that the published CSV link is still accessible."
    )
    st.exception(error)
    st.stop()


# ============================================================
# 5. COUNTRY ISO-3 MAPPING
# ============================================================

country_overrides = {
    "United States": "USA",
    "South Korea": "KOR",
    "Laos": "LAO",
    "Turkey": "TUR",
    "Czech Republic": "CZE",
    "Cape Verde": "CPV",
    "Sao Tome and Principe": "STP",
    "Saint Lucia": "LCA",
    "Trinidad and Tobago": "TTO",
    "Hong Kong": "HKG",
    "Northern Ireland": "GBR",
}


def get_iso3(country):
    """Convert country names into ISO-3 codes."""

    if pd.isna(country):
        return None

    if country in country_overrides:
        return country_overrides[country]

    try:
        return pycountry.countries.lookup(country).alpha_3
    except LookupError:
        return None


travel_df["iso3"] = travel_df["country"].apply(get_iso3)


# ============================================================
# 6. COUNTRY AND DESTINATION DATASETS
# ============================================================

country_summary = (
    travel_df
    .dropna(subset=["country"])
    .groupby("country", as_index=False)
    .agg(
        iso3=("iso3", "first"),
        continent=("continent", "first"),
        status=(
            "status",
            lambda values: (
                "visited"
                if (values == "visited").any()
                else "bucketlist"
            ),
        ),
    )
)

destination_df = travel_df[
    travel_df["status"] == "visited"
].copy()

bucket_list_df = country_summary[
    country_summary["status"] == "bucketlist"
].copy()


# ============================================================
# 7. CITY INFORMATION FOR MAP HOVER
# ============================================================

cities_by_country = (
    destination_df
    .dropna(subset=["iso3"])
    .groupby("iso3")["city"]
    .apply(
        lambda cities: ", ".join(
            sorted(cities.dropna().unique())
        )
        if cities.notna().any()
        else "No cities recorded yet"
    )
    .reset_index(name="cities_visited")
)

map_status = (
    country_summary
    .dropna(subset=["iso3"])
    .groupby("iso3", as_index=False)
    .agg(
        country=("country", "first"),
        status=(
            "status",
            lambda values: (
                "Visited"
                if (values == "visited").any()
                else "Bucketlist"
            ),
        ),
    )
)

map_status = map_status.merge(
    cities_by_country,
    on="iso3",
    how="left",
)

map_status["cities_visited"] = (
    map_status["cities_visited"]
    .fillna("No cities recorded yet")
)


# ============================================================
# 8. BUILD WORLD MAP DATA
# ============================================================

world_countries = pd.DataFrame([
    {
        "iso3": country.alpha_3,
        "country": country.name,
    }
    for country in pycountry.countries
])

# Add any ISO codes not included in the standard country list
extra_countries = (
    country_summary[
        ~country_summary["iso3"].isin(world_countries["iso3"])
    ][["iso3", "country"]]
    .dropna()
    .drop_duplicates(subset=["iso3"])
)

world_countries = pd.concat(
    [world_countries, extra_countries],
    ignore_index=True,
)

world_map_df = world_countries.merge(
    map_status[
        ["iso3", "status", "cities_visited"]
    ],
    on="iso3",
    how="left",
)

world_map_df["status"] = (
    world_map_df["status"]
    .fillna("Not recorded")
)

world_map_df["cities_visited"] = (
    world_map_df["cities_visited"]
    .fillna("No cities recorded")
)


# ============================================================
# 9. HOMEPAGE STATISTICS
# ============================================================

countries_visited = country_summary[
    country_summary["status"] == "visited"
]["country"].nunique()

bucket_list_count = bucket_list_df["country"].nunique()

visits_by_country = (
    destination_df
    .groupby("country")["no_of_visits"]
    .sum()
    .sort_values(ascending=False)
)

if not visits_by_country.empty:
    most_visited_country = visits_by_country.index[0]
    most_visited_count = int(visits_by_country.iloc[0])

    most_visited_display = (
        f"{most_visited_country}"
    )
else:
    most_visited_display = "—"

countries_lived = destination_df[
    destination_df["visit_type"].str.lower() == "living"
]["country"].nunique()


# ============================================================
# 10. SEVEN WONDERS DATA
# ============================================================

seven_wonders = [
    {
        "name": "Christ the Redeemer",
        "aliases": ["christ the redeemer", "christ the reedemer"],
    },
    {
        "name": "Great Wall of China",
        "aliases": ["great wall", "great wall of china"],
    },
    {
        "name": "Colosseum",
        "aliases": ["colosseum", "the colosseum"],
    },
    {
        "name": "Chichen Itza",
        "aliases": ["chichen itza", "chichén itzá"],
    },
    {
        "name": "Petra",
        "aliases": ["petra"],
    },
    {
        "name": "Machu Picchu",
        "aliases": ["machu picchu"],
    },
    {
        "name": "Taj Mahal",
        "aliases": ["taj mahal"],
    },
]


def normalise_name(value):
    """Make names easier to compare."""

    value = str(value).lower().strip()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return value.strip()


recorded_wonders = set(
    destination_df["wonder"]
    .dropna()
    .apply(normalise_name)
)

for wonder in seven_wonders:
    wonder["visited"] = any(
        normalise_name(alias) in recorded_wonders
        for alias in wonder["aliases"]
    )

wonders_visited = sum(
    wonder["visited"] for wonder in seven_wonders
)

wonder_progress = wonders_visited / len(seven_wonders)


def find_wonder_image(wonder):
    """
    Find an image in the wonders folder by matching
    its filename to the wonder name or its aliases.
    """

    if not WONDER_IMAGE_DIR.exists():
        return None

    possible_names = [
        wonder["name"],
        *wonder["aliases"],
    ]

    possible_names = [
        normalise_name(name).replace(" ", "")
        for name in possible_names
    ]

    supported_extensions = {
        ".jpg", ".jpeg", ".png", ".webp"
    }

    for image_path in WONDER_IMAGE_DIR.iterdir():

        if image_path.suffix.lower() not in supported_extensions:
            continue

        filename = normalise_name(
            image_path.stem
        ).replace(" ", "")

        if any(
            name in filename or filename in name
            for name in possible_names
        ):
            return image_path

    return None


# ============================================================
# 11. HOMEPAGE INTRODUCTION
# ============================================================

st.markdown(
    """
    <div class="intro-title">
        Destinations Explored.
    </div>
    <div class="intro-subtitle">
        The best stories come from the messiest moments.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 12. KPI STATISTICS
# ============================================================

stats = [
    ("Countries & territories visited", countries_visited),
    ("Bucketlist destinations", bucket_list_count),
    ("Seven Wonders", f"{wonders_visited}/7"),
    ("Most Visited Country", most_visited_display),
    ("Places called Home", countries_lived),
]

stat_columns = st.columns(5)

for index, (label, value) in enumerate(stats):

    with stat_columns[index]:

        st.markdown(
            f"""
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
            """,
            unsafe_allow_html=True,
        )


st.markdown("---")


# ============================================================
# 13. INTERACTIVE WORLD MAP
# ============================================================

st.markdown(
    '<div class="section-heading">The World, According to Me</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="section-caption">
        Every country has a story. Hover over the map to explore.
    </div>
    """,
    unsafe_allow_html=True,
)

map_colours = {
    "Visited": SAGE,
    "Bucketlist": TERRACOTTA,
    "Not recorded": MOSS,
}

fig_map = px.choropleth(
    world_map_df,
    locations="iso3",
    color="status",
    hover_name="country",
    hover_data={
        "iso3": False,
        "status": True,
        "cities_visited": True,
    },
    locationmode="ISO-3",
    color_discrete_map=map_colours,
    category_orders={
        "status": [
            "Visited",
            "Bucketlist",
            "Not recorded",
        ]
    },
)

fig_map.update_geos(
    projection_type="natural earth",
    showframe=False,
    showcoastlines=True,
    coastlinecolor=BORDER,
    showcountries=True,
    countrycolor=BG,
    showocean=False,
    showland=True,
    landcolor=MOSS,
    bgcolor=BG,
)

fig_map.update_layout(
    paper_bgcolor=BG,
    plot_bgcolor=BG,
    font_color=TEXT,
    margin=dict(l=0, r=0, t=10, b=10),
    height=550,
    legend_title_text="Travel status",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=0.02,
        xanchor="center",
        x=0.5,
    ),
)

fig_map.update_traces(
    hovertemplate=(
        "<b>%{hovertext}</b><br>"
        "Status: %{customdata[1]}<br>"
        "Cities: %{customdata[2]}"
        "<extra></extra>"
    )
)

st.plotly_chart(
    fig_map,
    use_container_width=True,
    config={"displayModeBar": False},
)


# ============================================================
# 14. SECONDARY VISUAL SECTION
#     CONTINENT DONUT | SEVEN WONDERS | TOP FIVE
# ============================================================

st.markdown("---")

left_col, centre_col, right_col = st.columns(
    [1, 1.15, 1],
    gap="large",
)


# ------------------------------------------------------------
# LEFT: CONTINENT DONUT
# ------------------------------------------------------------

with left_col:

    st.markdown(
        '<div class="section-heading">Continents</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-caption">Where the journey has taken me</div>',
        unsafe_allow_html=True,
    )

    continent_counts = (
        destination_df
        .dropna(subset=["continent"])
        .groupby("continent")
        .size()
        .reset_index(name="destinations")
        .sort_values("destinations", ascending=False)
    )

    if not continent_counts.empty:

        continent_colours = [
          SAGE,
          TERRACOTTA,
          GOLD,
          MUTED,
          "#6F8F83",
          "#A66F59",
          "#C4B18A",
          "#607B72",
          "#D6D0C2",
        ]

        continent_fig = px.pie(
          continent_counts,
          names="continent",
          values="destinations",
          hole=0.58,
          color="continent",
          color_discrete_sequence=continent_colours,
    )
        

        continent_fig.update_traces(
            textposition="inside",
            texttemplate="%{percent:.0%}",
            textfont=dict(
                color=TEXT,
                size=12,
            ),
            hovertemplate=(
                "<b>%{label}</b><br>"
                "%{value} destinations<br>"
                "%{percent:.1%}"
                "<extra></extra>"
            ),
        )

        continent_fig.update_layout(
            paper_bgcolor=BG,
            plot_bgcolor=BG,
            font_color=TEXT,
            showlegend=False,
            margin=dict(l=0, r=0, t=10, b=10),
            height=420,
        )

        st.plotly_chart(
            continent_fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

        # Compact continent legend
        legend_items = continent_counts[
            "continent"
        ].tolist()

        legend_columns = st.columns(2)

        for index, continent in enumerate(legend_items):

            with legend_columns[index % 2]:
                st.markdown(
                    f"<div class='story-caption'>"
                    f"• {continent}</div>",
                    unsafe_allow_html=True,
                )

    else:
        st.info("Your continent breakdown will appear here.")


# ------------------------------------------------------------
# CENTRE: SEVEN WONDERS TRACKER
# ------------------------------------------------------------

with centre_col:

    st.markdown(
        '<div class="section-heading">Seven Wonders</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-caption">Four down, three to go</div>',
        unsafe_allow_html=True,
    )

    st.progress(wonder_progress)

    st.markdown(
        f"""
        <div class="wonder-status">
            {wonders_visited} of 7 wonders visited
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    for wonder in seven_wonders:

        image_path = find_wonder_image(wonder)

        image_col, name_col, status_col = st.columns(
            [0.75, 2.5, 1.0],
            vertical_alignment="center",
        )

        with image_col:

            if image_path is not None:

                try:
                    wonder_image = Image.open(image_path)

                    if not wonder["visited"]:
                        wonder_image = ImageOps.grayscale(
                            wonder_image
                        )

                    st.image(
                        wonder_image,
                        width=52,
                    )

                except Exception:
                    st.markdown("🌍")

            else:
                st.markdown("🌍")

        with name_col:

            st.markdown(
                f"<div class='wonder-name'>"
                f"{wonder['name']}</div>",
                unsafe_allow_html=True,
            )

        with status_col:

            if wonder["visited"]:
                st.markdown(
                    "<div class='wonder-status'>"
                    "✓ Visited</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div class='wonder-status'>"
                    "To explore</div>",
                    unsafe_allow_html=True,
                )

        st.markdown(
            f"<hr style='margin: 0.35rem 0; "
            f"border-color: {BORDER};'>",
            unsafe_allow_html=True,
        )


# ------------------------------------------------------------
# RIGHT: TOP FIVE MOST VISITED COUNTRIES
# ------------------------------------------------------------

with right_col:

    st.markdown(
        '<div class="section-heading">Top Five</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-caption">Countries visited most often</div>',
        unsafe_allow_html=True,
    )

    top_five = (
        visits_by_country
        .head(5)
        .reset_index()
    )

    top_five.columns = ["country", "visits"]

    if not top_five.empty:

        top_five = top_five.sort_values(
            "visits",
            ascending=True,
        )

        bar_fig = px.bar(
            top_five,
            x="visits",
            y="country",
            orientation="h",
            text="visits",
        )

        bar_fig.update_traces(
            marker_color=SAGE,
            textposition="outside",
            textfont=dict(color=TEXT),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "%{x} recorded visits"
                "<extra></extra>"
            ),
        )

        bar_fig.update_layout(
            paper_bgcolor=BG,
            plot_bgcolor=BG,
            font_color=TEXT,
            height=420,
            margin=dict(l=0, r=25, t=10, b=10),
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                title=None,
            ),
            yaxis=dict(
                showgrid=False,
                title=None,
                tickfont=dict(size=11,color=TEXT,),
            ),
            showlegend=False,
        )

        st.plotly_chart(
            bar_fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    else:
        st.info("Your most visited countries will appear here.")





# ============================================================
# 15. DYNAMIC TRAVEL STORIES
# ============================================================

st.markdown("---")

st.markdown(
    '<div class="section-heading">Travel Stories</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="section-caption">
        The moments, mishaps and memories behind the destinations.
    </div>
    """,
    unsafe_allow_html=True,
)

# Retrieve published blog posts directly from the Google Sheet
blog_posts = (
    travel_df[
        travel_df["blog_titles"].notna()
        & travel_df["blog_url"].notna()
    ][["country", "blog_titles", "blog_url"]]
    .copy()
)

# Remove accidental whitespace and duplicate entries
for column in ["country", "blog_titles", "blog_url"]:
    blog_posts[column] = blog_posts[column].astype("string").str.strip()

blog_posts = (
    blog_posts[
        blog_posts["blog_titles"].ne("")
        & blog_posts["blog_url"].ne("")
    ]
    .drop_duplicates(
        subset=["blog_titles", "blog_url"]
    )
    .reset_index(drop=True)
)

# Display stories in rows of three
if not blog_posts.empty:

    for start in range(0, len(blog_posts), 3):

        story_columns = st.columns(3)

        for index, column in enumerate(story_columns):

            post_index = start + index

            if post_index >= len(blog_posts):
                continue

            post = blog_posts.iloc[post_index]

            with column:

                st.markdown(
                    f"""
                    <div class="story-card">
                        <div class="story-title">
                            {post['blog_titles']}
                        </div>
                        
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.link_button(
                    "Read the story",
                    post["blog_url"],
                    use_container_width=True,
                )

else:

    st.info(
        "Your travel stories will appear here once "
        "you add blog titles and URLs to your Google Sheet."
    )



# ============================================================
# 16. FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    f"""
    <div style="
        text-align: center;
        color: {MUTED};
        font-size: 0.8rem;
        padding: 1rem 0;
    ">
        The Faceless Traveller · A personal travel journal
    </div>
    """,
    unsafe_allow_html=True,
)
