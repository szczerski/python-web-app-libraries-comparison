import streamlit as st
from rembg import remove
from PIL import Image
import io


def main():
    st.title("Background Remover")

    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

    col1, col2 = st.columns(2)
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        with col1:
            st.image(
                image, caption="Uploaded Image", use_column_width=False, width=300
            )

        output = remove(image)

        img_byte_arr = io.BytesIO()
        output.save(img_byte_arr, format="PNG")
        img_byte_arr = img_byte_arr.getvalue()

        with col2:
            st.image(
                output,
                caption="Image with Background Removed",
                use_column_width=False,
                width=300,
            )

            st.download_button(
                label="Download Image",
                data=img_byte_arr,
                file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_background_removed.png",
                mime="image/png",
                help="Download the image with the background removed."
            )


if __name__ == "__main__":
    main()
