from taipy.gui import Gui, notify

text = "1"

# Definition of the page
page = """
# Make a square of a number

<|{text}|input|label=Enter a number:|>
<br/>
<|{calculate_square(text)}|>

<|Run local|button|on_action=on_button_action|>
<|Reset|button|on_action=on_reset_action|>
"""

def calculate_square(value):
    try:
        number = int(value)
        return f"Square of {number} is {number ** 2}"
    except ValueError:
        return "Please enter a valid number"

def on_button_action(state):
    result = calculate_square(state.text)
    notify(state, 'success', result)

def on_reset_action(state):
    state.text = "1"
    notify(state, 'info', 'Input reset to 1')

def on_change(state, var_name, var_value):
    if var_name == "text":
        state.update()

# Add this line before creating the Gui instance

gui = Gui(page=page)
gui.run(port=5009, use_reloader=True, favicon="🔢")
