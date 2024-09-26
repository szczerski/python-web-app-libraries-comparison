import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from pmdarima import auto_arima
from sklearn.metrics import mean_squared_error
from math import sqrt
import warnings
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline


# Dictionary to store year and number of seasons
tv_seasons = {}

data = [
    "1950:1",
    "1951:2",
    "1952:2",
    "1953:2",
    "1954:2",
    "1955:3",
    "1956:4",
    "1957:4",
    "1958:4",
    "1959:7",
    "1960:11",
    "1961:11",
    "1962:10",
    "1963:10",
    "1964:8",
    "1965:6",
    "1966:7",
    "1967:9",
    "1968:11",
    "1969:11",
    "1970:10",
    "1971:10",
    "1972:13",
    "1973:12",
    "1974:13",
    "1975:16",
    "1976:22",
    "1977:26",
    "1978:26",
    "1979:27",
    "1980:24",
    "1981:23",
    "1982:23",
    "1983:22",
    "1984:18",
    "1985:19",
    "1986:21",
    "1987:28",
    "1988:33",
    "1989:38",
    "1990:41",
    "1991:41",
    "1992:39",
    "1993:41",
    "1994:48",
    "1995:55",
    "1996:59",
    "1997:66",
    "1998:69",
    "1999:67",
    "2000:72",
    "2001:79",
    "2002:95",
    "2003:103",
    "2004:121",
    "2005:142",
    "2006:164",
    "2007:169",
    "2008:185",
    "2009:218",
    "2010:226",
    "2011:245",
    "2012:247",
    "2013:248",
    "2014:253",
    "2015:251",
    "2016:236",
    "2017:235",
    "2018:235",
    "2019:215",
    "2020:170",
    "2021:168",
    "2022:165",
    "2023:119",
]

# Insert data into tv_seasons dictionary
for entry in data:
    year, number_of_seasons = entry.split(":")
    if year.isdigit():
        tv_seasons[int(year)] = int(number_of_seasons)

# Convert to DataFrame for easier manipulation
df = pd.DataFrame(list(tv_seasons.items()), columns=["Year", "Number of Seasons"])
df["Year"] = df["Year"].astype(str).str.replace(",", "")
df.set_index("Year", inplace=True)

# Streamlit UI
st.title("US TV Seasons by Year")
st.write(df)

# Slider for future trends
years_ahead = st.slider("Select number of years to project into the future:", 1, 15, 5)


@st.cache_data
def evaluate_arima_model(X, arima_order):
    # Prepare training dataset
    train_size = int(len(X) * 0.66)
    train, test = X[0:train_size], X[train_size:]
    history = [x for x in train]
    # Make predictions
    predictions = []
    for t in range(len(test)):
        model = ARIMA(history, order=arima_order)
        model_fit = model.fit()
        yhat = model_fit.forecast()[0]
        predictions.append(yhat)
        history.append(test[t])
    # Ensure predictions are non-negative
    predictions = [
        max(0, yhat) for yhat in predictions
    ]  # Ensure no negative predictions
    # Calculate out of sample error
    rmse = sqrt(mean_squared_error(test, predictions))
    return rmse


@st.cache_data
def evaluate_models(dataset, p_values, d_values, q_values):
    dataset = dataset.astype(float)
    best_score, best_cfg = float("inf"), None
    total_combinations = len(p_values) * len(d_values) * len(q_values)

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, p in enumerate(p_values):
        for d in d_values:
            for q in q_values:
                order = (p, d, q)
                try:
                    rmse = evaluate_arima_model(dataset, order)
                    if rmse < best_score:
                        best_score, best_cfg = rmse, order
                    status_text.text(f"ARIMA{order} RMSE={rmse:.3f}")
                except:
                    continue
                progress = (
                    i * len(d_values) * len(q_values) + d * len(q_values) + q + 1
                ) / total_combinations
                progress_bar.progress(progress)

    status_text.text(f"Best ARIMA{best_cfg} RMSE={best_score:.3f}")
    return best_cfg


# Evaluate parameters
with st.spinner("Evaluating ARIMA models..."):
    p_values = [0, 1, 2]  # Reduced parameter space
    d_values = range(0, 2)
    q_values = range(0, 2)
    warnings.filterwarnings("ignore")
    best_order = evaluate_models(
        df["Number of Seasons"].values, p_values, d_values, q_values
    )

# Fit the ARIMA model
model = ARIMA(df["Number of Seasons"], order=best_order)
results = model.fit()

# Make future predictions using ARIMA
forecast = results.forecast(steps=years_ahead)
forecast = [max(0, f) for f in forecast]  # Ensure no negative forecasts
future_years = range(int(df.index[-1]) + 1, int(df.index[-1]) + years_ahead + 1)

# Create DataFrame for predictions
future_df = pd.DataFrame({"Year": future_years, "Projected Seasons (ARIMA)": forecast})

# Combine historical and future data
combined_df = pd.concat([df, future_df.set_index("Year")])

# Plotting ARIMA predictions
st.subheader("Historical Data and ARIMA Predictions")
st.line_chart(combined_df)

# Display ARIMA model summary
st.subheader("ARIMA Model Summary:")
st.text(results.summary())

# Make future predictions using another time series model (e.g., SARIMAX)
# Replace the polynomial regression model with SARIMAX
model_sarimax = SARIMAX(df["Number of Seasons"], order=best_order)
results_sarimax = model_sarimax.fit()

# Make future predictions using SARIMAX
forecast_sarimax = results_sarimax.forecast(steps=years_ahead)
forecast_sarimax = [max(0, f) for f in forecast_sarimax]  # Ensure no negative forecasts

# Add SARIMAX predictions to the DataFrame
future_df["Projected Seasons (SARIMAX)"] = forecast_sarimax

# Update combined DataFrame
combined_df = pd.concat([df, future_df.set_index("Year")])

# Plotting all predictions
st.subheader("Historical Data with ARIMA, SARIMAX, and Polynomial Regression Predictions")
st.line_chart(combined_df)

# Display explicit predictions for SARIMAX
st.subheader(f"Predictions for the Next {years_ahead} Years (SARIMAX):")
for i in range(years_ahead):
    year = future_years[i]
    sarimax_pred = round(future_df["Projected Seasons (SARIMAX)"][i], 2)
    st.write(f"Year {year}:")
    st.write(f"  - SARIMAX prediction: {sarimax_pred} seasons")

# Comparison of predictions
st.subheader("Comparison of All Predictions: ARIMA, SARIMAX, and Polynomial Regression Predictions:")
st.write(future_df)
