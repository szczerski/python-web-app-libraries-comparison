from taipy import Gui
import pandas as pd

data = pd.DataFrame({
    'first column': [1, 2, 3, 4],
    'second column': [10, 20, 30, 40]
})

page = """
<|layout|columns=1 1|
# DataFrame: <|{data}|table|>
# Pie chart: <|{data}|chart|type=pie|values=second column|labels=first column|width=100%|height=50%|>
|>
"""

gui = Gui(page=page)
gui.run(port=5009, use_reloader=True)