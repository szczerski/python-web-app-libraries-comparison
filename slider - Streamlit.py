import streamlit as st

x = st.slider("x")
st.header(f":red[{x}] squared is :blue[{x * x}]")


