import streamlit as st
import pandas as pd

def notify(state, type, message):
    state.show_messages = True
    state.message_type = type
    state.message = message

def on_reset_action(state):
    state.text = "1"
    notify(state, 'info', 'Input reset to 1')

def main():
    st.set_page_config(page_title="Number Squarer", page_icon="🔢")
    st.title("Make a square of a number")

    if 'show_messages' in st.session_state and st.session_state.show_messages:
        message_type = st.session_state.message_type
        message = st.session_state.message
        if message_type == 'success':
            st.success(message)
        elif message_type == 'info':
            st.info(message)
        st.session_state.show_messages = False

    text = st.text_input("Enter a number:", value=st.session_state.get('text', "1"))

    if text.isdigit():
        square = int(text) ** 2
        st.write(f"Square of {text} is {square}")
    else:
        st.write("Please enter a valid number")

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Run local"):
            if text.isdigit():
                st.session_state.squared_value = int(text) ** 2
                notify(st.session_state, 'success', f"Squared {st.session_state.squared_value}")
                st.rerun()

    with col2:
        if st.button("Reset"):
            on_reset_action(st.session_state)
            st.rerun()

if __name__ == "__main__":
    main()

