import pandas as pd
from datetime import datetime
from taipy.gui import Gui

logo = "logo.png"
df = pd.read_csv("medallists.csv")

df = df[df["team_gender"].isna()]

print("df ROWS:", df.shape[0])

df = df.drop(
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


gold_medals = medals_by_country[medals_by_country["Medal"] == "Gold Medal"]
country_gender_medals = {}

for index, row in medals_by_country.iterrows():
    country = row["Country"]
    gender = row["Gender"]
    if country not in country_gender_medals:
        country_gender_medals[country] = {}
    if gender not in country_gender_medals[country]:
        country_gender_medals[country][gender] = 0
    country_gender_medals[country][gender] += 1

country_gender_medals = dict(
    sorted(
        country_gender_medals.items(),
        key=lambda x: sum(x[1].values()),
        reverse=True,
    )
)



medals_by_country = df[
    ["name", "country", "medal_type", "gender", "discipline", "birth_date"]
]

country_gender_medals = (
    medals_by_country.groupby(["country", "gender"])["medal_type"]
    .count()
    .unstack(fill_value=0)
    .reset_index()
)
country_gender_medals.columns.name = None
country_gender_medals = country_gender_medals.rename(columns={"country": "Country"})

country_gender_medals_five_female = country_gender_medals.sort_values(
    "Female", ascending=False
).head(5)
country_gender_medals_five_male = country_gender_medals.sort_values(
    "Male", ascending=False
).head(5)


def calculate_age(birth_date):
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

df_ages = pd.DataFrame(age_counts.items(), columns=["Age", "Athletes"])


def table_style(state, index, row):
    return "highlight-row" if row.Medal == "Gold Medal" else ""


table_properties = {
    "class_name": "rows-bordered rows-similar",  # optional
    "style": table_style,
}


root_md = """
<|navbar|>
# 🗼 Paris 2024 Olympics: Medal Distribution for Individual Athletes 🏅

"""

page_main = """
<|layout|gap=50px|columns=500px 500px|columns[mobile]=1 1|

<|{logo}|image|>

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



|>
"""
medals_by_country.columns = [
    "Name",
    "Country",
    "Medal",
    "Gender",
    "Discipline",
    "Birth Date",
]
page1_md = """
## 🏅 Medals by Athletes
<|{medals_by_country}|table|filter=True|properties=table_properties|>
"""

page2_md = """
## ⏳ Age Distribution of Olympic Athletes
<|layout|columns=300px 900px|columns[mobile]=1 1|
<|
### Key Insights:

- **Peak Age Group (25-30 years):** The highest number of athletes falls between the ages of 25 to 30, indicating this is the prime age range for peak athletic performance in the Olympics.
- **Outliers (45-55 years):** There are very few athletes above 45, likely representing competitors in sports where age may be less of a factor or individuals with exceptional longevity in their careers.
|>

<|{df_ages}|chart|type=bar|>
|>
"""
page3_md = """
## 🚻 Comparison of Female vs. Male Medals
<|layout|columns=300px 450px 450px|columns[mobile]=1 1|
<|
### Key Insights:

- **The United States** and **China** dominated in both male and female categories.
- **Australia** had strong female participation, while **France** excelled more with male athletes.
- **Great Britain** and **Japan** showed more balanced or male-focused achievements.
|>

<|{country_gender_medals_five_female}|chart|type=pie|values=Female|labels=Country|title=Female Medals|>

<|{country_gender_medals_five_male}|chart|type=pie|values=Male|labels=Country|title=Male Medals|>
|>
"""

country_coordinates = pd.read_csv("country_coordinates.csv")
medals_total = pd.read_csv("medals_total.csv")

medals_by_country_with_lat_lon = pd.merge(
    medals_total, country_coordinates, left_on="country_code", right_on="country_code"
)


medals_by_country_with_lat_lon["text"] = (
    medals_by_country_with_lat_lon["country_code"]
    + ": "
    + medals_by_country_with_lat_lon["Total"].astype(str)
    + " medals"
)

marker = {
    "size": "Total",
    "sizemode": "area",
    "sizeref": 2.0 * max(medals_by_country_with_lat_lon["Total"]) / (40.0**2),
    "sizemin": 4,
    "color": "Total",
    "colorscale": "Viridis",
    "colorbar": {"title": "Total Medals"},
    "showscale": True,
}

layout = {
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

page4_md = """
## 🌎 Map of Total Medals by Country

<|{medals_by_country_with_lat_lon}|chart|type=scattergeo|mode=markers|lat=latitude|lon=longitude|marker={marker}|text=text|hovertext=text|hoverinfo=text|layout={layout}|>

"""

pages = {
    "/": root_md,
    "Paris": page_main,
    "Medals": page1_md,
    "Age": page2_md,
    "Gender": page3_md,
    "Map": page4_md,
}

gui = Gui(pages=pages).run()
