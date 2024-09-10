from taipy.gui import Gui

value = 0

css = """
<style>
.taipy-dark {
    margin-top: 100px;
    text-align: center;
    background-color: black;
}
.input-value {
    color: #ff3424;
    font-size: 20px;
}
.result {
    color: #3e98f8;
    font-size: 20px;
}
.MuiBox-root {
    background-color: black;
}
</style>
"""
page = f"""
{css}
<|{{value}}|slider|min=0|max=100|><br />
<span class="input-value"><|{{value}}|text|raw|></span> 
squared is <span class="result"><|{{value ** 2}}|text|raw|></span>
"""

gui = Gui(page=page)
gui.run(port=5009, use_reloader=True)
