import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

df = pd.DataFrame({
    'first column': [1, 2, 3, 4],
    'second column': [10, 20, 30, 40]
})

col1, col2 = st.columns(2)

with col1:
    st.write("DataFrame:")
    st.write(df)

with col2:
    st.write("Pie Chart:")
    fig = px.pie(df, values='second column', names='first column')
    st.plotly_chart(fig, use_container_width=True)
    
