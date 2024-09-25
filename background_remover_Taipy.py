from taipy.gui import Gui, notify
from rembg import remove
from PIL import Image
import os
from pathlib import Path

processed_image = None
img_name = None
original_image_data = None

# placeholder for uploaded image
uploaded_image = "./assets/one.png"
processed_image_path = "./assets/one.png"


def downloaded_image(state):

    if state.uploaded_image:
        try:
            img_to_rm = Image.open(state.uploaded_image)
            img_name = os.path.splitext(os.path.basename(state.uploaded_image))[0]
            with open(state.uploaded_image, "rb") as f:
                original_image_data = f.read()

            processed_image = remove(img_to_rm)

            download_folder = str(Path.home() / "Downloads")

            # Generate a unique filename
            base_filename = f"{img_name}_processed.png"
            counter = 1
            filename = base_filename
            while os.path.exists(os.path.join(download_folder, filename)):
                filename = f"{img_name}_processed_{counter}.png"
                counter += 1

            # Save the processed image to the download folder
            full_path = os.path.join(download_folder, filename)
            processed_image.save(full_path, format="PNG")

            # Update state variables
            state.img_name = img_name
            state.processed_image_path = full_path
            state.original_image_data = original_image_data

            notify(state, "success", f"Image processed and saved: {full_path}")

        except Exception as e:
            notify(state, "error", f"An error occurred: {e}")


page = """
# Background Remover
<|{uploaded_image}|file_selector|label=Choose an image...|extensions=.png,.jpg,.jpeg|>
<|button|label=Download File|on_action=downloaded_image|>

<|layout|1 2|
<|{uploaded_image}|image|label=Uploaded Image|width=300px|active=False|>
<|{processed_image_path}|image|label=Uploaded Image|width=300px|>
|>
"""

if __name__ == "__main__":
    gui = Gui(page)
    gui.run()
