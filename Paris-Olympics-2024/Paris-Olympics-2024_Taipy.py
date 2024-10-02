import pandas as pd
import plotly.graph_objs as go
from datetime import datetime
from taipy.gui import Gui
from typing import Dict, Any

LOGO = "logo.png"
MEDAL_CSV = "medallists.csv"
COUNTRY_COORDINATES_CSV = "country_coordinates.csv"
MEDALS_TOTAL_CSV = "medals_total.csv"

def load_and_process_data() -> Dict[str, Any]:
    """Load and process all necessary data for the application."""
    df = pd.read_csv(MEDAL_CSV)
    df = df[df["team_gender"].isna()].drop(
        columns=[
            "country_code",
            "event",
            "url_event",
            "event_type",
            "medal_code",
            "medal_date",
            "team_gender",
        ]
    )

    medals_by_country = df[
        ["name", "country", "medal_type", "gender", "discipline", "birth_date"]
    ]
    medals_by_country.columns = [
        "Name",
        "Country",
        "Medal",
        "Gender",
        "Discipline",
        "Birth Date",
    ]

    country_gender_medals = (
        medals_by_country.groupby(["Country", "Gender"])["Medal"]
        .count()
        .unstack(fill_value=0)
        .reset_index()
    )
    country_gender_medals.columns.name = None

    country_gender_medals_five_female = country_gender_medals.nlargest(5, "Female")
    country_gender_medals_five_male = country_gender_medals.nlargest(5, "Male")

    age_counts = calculate_age_distribution(df)
    df_ages = pd.DataFrame(age_counts.items(), columns=["Age", "Athletes"])

    medals_total = pd.read_csv(MEDALS_TOTAL_CSV)
    country_coordinates = pd.read_csv(COUNTRY_COORDINATES_CSV)
    medals_by_country_with_lat_lon = pd.merge(
        medals_total, country_coordinates, on="country_code"
    )
    medals_by_country_with_lat_lon["text"] = (
        medals_by_country_with_lat_lon["country_code"]
        + ": "
        + medals_by_country_with_lat_lon["Total"].astype(str)
        + " medals"
    )

    return {
        "medals_by_country": medals_by_country,
        "country_gender_medals_five_female": country_gender_medals_five_female,
        "country_gender_medals_five_male": country_gender_medals_five_male,
        "df_ages": df_ages,
        "medals_by_country_with_lat_lon": medals_by_country_with_lat_lon,
    }


def calculate_age_distribution(df: pd.DataFrame) -> Dict[int, int]:
    """Calculate the age distribution of athletes."""

    def calculate_age(birth_date: str) -> int:
        if pd.isna(birth_date):
            return None
        try:
            birth_date = datetime.strptime(birth_date, "%Y-%m-%d")
            return datetime.now().year - birth_date.year
        except ValueError:
            return None

    age_series = df["birth_date"].apply(calculate_age)
    age_counts = age_series.value_counts().sort_index().to_dict()
    age_counts.pop(None, None)
    return age_counts


def table_style(state: Any, index: int, row: pd.Series) -> str:
    """Define the style for table rows."""
    return "highlight-row" if row.Medal == "Gold Medal" else ""


def create_map_layout() -> Dict[str, Any]:
    """Create the layout for the medal map."""
    return {
        "geo": {
            "showland": True,
            "landcolor": "rgb(217, 217, 217)",
            "showocean": True,
            "oceancolor": "rgb(204, 229, 255)",
            "showcountries": True,
            "countrycolor": "rgb(204, 204, 204)",
            "projection": {"scale": 1.3},
        },
        "title": "Olympic Medals by Country",
        "height": 700,
    }


def create_marker_settings(
    medals_by_country_with_lat_lon: pd.DataFrame,
) -> Dict[str, Any]:
    """Create marker settings for the medal map."""
    return {
        "size": "Total",
        "sizemode": "area",
        "sizeref": 2.0 * medals_by_country_with_lat_lon["Total"].max() / (40.0**2),
        "sizemin": 4,
        "color": "Total",
        "colorscale": "Viridis",
        "colorbar": {"title": "Total Medals"},
        "showscale": True,
    }


data = load_and_process_data()

table_properties = {
    "class_name": "rows-bordered rows-similar",
    "style": table_style,
}

description_page_1 = """
- **Location:** Paris, France  
- **Motto:** Games Wide Open (*French: Ouvrons Grand les Jeux*)  
- **Nations:** 204 (including the AIN and EOR teams)  
- **Athletes:** 10,714  
- **Events:** 329 in 32 sports (48 disciplines)  
- **Opening:** 26 July 2024  
- **Closing:** 11 August 2024  
- **Opened by:** Emmanuel Macron (President of France)  
- **Closed by:** Thomas Bach (President of the International Olympic Committee)  
- **Cauldron Lighters:** Teddy Riner, Marie-José Pérec  
- **Venues:** Jardins du Trocadéro and the Seine (Opening ceremony) and Stade de France (Closing ceremony)
"""

description_page_2 = """
### Key Insights:

- **Peak Age Group (25-30 years):** The highest number of athletes falls between the ages of 25 to 30, indicating this is the prime age range for peak athletic performance in the Olympics.
- **Outliers (45-55 years):** There are very few athletes above 45, likely representing competitors in sports where age may be less of a factor or individuals with exceptional longevity in their careers.
"""

description_page_3 = """
### Key Insights:

- **The United States** and **China** dominated in both male and female categories.
- **Australia** had strong female participation, while **France** excelled more with male athletes.
- **Great Britain** and **Japan** showed more balanced or male-focused achievements.
"""

navbar = """
<|navbar|>
# 🗼 Paris 2024 Olympics: Medal Distribution for Individual Athletes 🏅
"""

page0 = """
<|layout|gap=50px|columns=500px 500px|columns[mobile]=1 1|
<|{LOGO}|image|>

<|{description_page_1}|text|mode=markdown|>
|>
"""

page1 = """
## 🏅 Medals by Athletes
<|{data["medals_by_country"]}|table|filter=True|properties=table_properties|>
"""

page2 = """
## ⏳ Age Distribution of Olympic Athletes
<|layout|columns=300px 900px|columns[mobile]=1 1|
<|{description_page_2}|text|mode=markdown|>

<|{data["df_ages"]}|chart|type=bar|>
|>
"""

page3 = """
## 🚻 Comparison of Female vs. Male Medals
<|layout|columns=300px 450px 450px|columns[mobile]=1 1|
<|{description_page_3}|text|mode=markdown|>

<|{data["country_gender_medals_five_female"]}|chart|type=pie|values=Female|labels=Country|title=Female Medals|>

<|{data["country_gender_medals_five_male"]}|chart|type=pie|values=Male|labels=Country|title=Male Medals|>
|>
"""

page4 = """
## 🌎 Map of Total Medals by Country
<|{data["medals_by_country_with_lat_lon"]}|chart|type=scattergeo|mode=markers|lat=latitude|lon=longitude|marker={create_marker_settings(data["medals_by_country_with_lat_lon"])}|text=text|hovertext=text|hoverinfo=text|layout={create_map_layout()}|>
"""

pages = {
    "/": navbar,
    "Paris": page0,
    "Medals": page1,
    "Age": page2,
    "Gender": page3,
    "Map": page4,
}

if __name__ == "__main__":
    gui = Gui(pages=pages)
    gui.run()
