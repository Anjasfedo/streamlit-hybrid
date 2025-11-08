import streamlit as st
import json
import numpy as np
import pandas as pd

# --- Sidebar Navigation ---
st.sidebar.title("Hybrid Steganography 🛡️")
st.sidebar.write("Select your steganography technique:")

# This radio button now selects the *steganography method*
selected_method = st.sidebar.radio(
    "Choose your method:",
    ("LSB", "PVD", "Hybrid (LSB + PVD)"), # Added a Hybrid option based on your title
    label_visibility="collapsed"
)

# --- Main Content Area ---
# We create the tabs for the two main flows: Embed and Extract
# These tabs will always be present.
tab_embed, tab_extract = st.tabs(["Embed Message 🖼️", "Extract Message 🕵️"])

# --- Embed Tab Content ---
with tab_embed:
    st.title(f"Embed using {selected_method}")
    
    # Now, the content inside this tab can change based on the selected method
    if selected_method == "LSB":
        
        # 1. Parameters Section
        with st.expander("Configure Parameters"):
            # Add LSB-specific parameters here
            lsb_bit_plane = st.number_input("LSB Bit Plane (e.g., 1-8)", min_value=1, max_value=8, value=1, key="lsb_bit_plane")
            # We create a dictionary for parameter download
            parameters_to_save = {"method": "LSB", "bit_plane": lsb_bit_plane}

        st.subheader("Message Input")
        col1, col2 = st.columns([0.6, 0.4]) # Give more space to the message area

        with col1:
            lsb_embed_msg= st.text_area("Your Secret Message", height=150, key="lsb_embed_msg", label_visibility="collapsed")
        
        with col2:
            with st.container(border=True):
                st.write("Dummy Message Helper")
                dummy_len = st.number_input("Message Length", min_value=10, value=100)
                if st.button("Generate Dummy Message"):
                    st.toast(f"Dummy message of length {dummy_len} generated!")
                    # In a real app, you'd update the text_area state here
        
        # 3. Cover Image (Full width)
        cover_image_file = st.file_uploader("Upload Cover Image", type=["png", "jpg", "bmp"], key="lsb_embed_img", label_visibility="collapsed")
                # Placeholder for image display
        if cover_image_file is not None:
            st.image(cover_image_file, caption="Uploaded Cover Image", use_container_width=True)
            
        # 4. Embed Button
        st.divider()
        embed_button = st.button("Embed Message", type="primary")

        # 5. Result Section (shown after embed button is clicked)
        if embed_button:
            st.subheader("Embedding Results")
            
            # This is where your actual embedding logic would run
            # For now, we'll use placeholders
            
            res_col1, res_col2 = st.columns(2)
            
            with res_col1:
                st.write("**Stego-Image**")
                # Placeholder for image display
                st.image("https://via.placeholder.com/400x400.png?text=Your+Stego-Image", caption="Steganographic Image")
                
                # Placeholder for image download
                st.download_button(
                    label="Download Image",
                    data=b"placeholder_image_data", # Replace with your actual image bytes
                    file_name="stego_image.png",
                    mime="image/png"
                )
            
            with res_col2:
                st.write("**Parameters Used**")
                
                message_bit_length = len(lsb_embed_msg.encode('utf-8')) * 8
                    
                parameters_to_save = {
                        "method": "LSB", 
                        "bit_plane": lsb_bit_plane,
                        "message_bit_length": message_bit_length # Added the new key
                }
                
                st.download_button(
                    label="Download Parameters",
                    data=parameters_to_save,
                    file_name="parameters.json",
                    mime="application/json"
                )
        
    elif selected_method == "PVD":
        st.write("This is where the **PVD Embedding** controls will go.")
        # Add PVD-specific embedding widgets here
        st.file_uploader("Upload Cover Image (PVD)", key="pvd_embed_img")
        st.text_area("Your Secret Message (PVD)", key="pvd_embed_msg")
        st.button("Embed with PVD", key="pvd_embed_btn")
        
    elif selected_method == "Hybrid (LSB + PVD)":
        st.write("This is where the **Hybrid Embedding** controls will go.")
        # Add Hybrid-specific embedding widgets here
        st.file_uploader("Upload Cover Image (Hybrid)", key="hybrid_embed_img")
        st.text_area("Your Secret Message (Hybrid)", key="hybrid_embed_msg")
        st.button("Embed with Hybrid", key="hybrid_embed_btn")

# --- Extract Tab Content ---
with tab_extract:
    st.title(f"Extract using {selected_method}")
    
    if selected_method == "LSB":
        
        # 1. Parameter Input
        with st.expander("Configure Parameters"):
            lsb_bit_plane_extract = st.number_input("LSB Bit Plane (e.g., 1-8)", min_value=1, max_value=8, value=1, key="lsb_bit_plane_extract")
            # You can also add a file uploader here for the .json parameter file

        # 1.5 Stego-Image Input (Essential)
        st.subheader("Upload Stego-Image")
        stego_image_file = st.file_uploader("Upload the image you want to extract from", type=["png", "jpg", "bmp"], key="lsb_extract_img", label_visibility="collapsed")

        if stego_image_file is not None:
            st.image(stego_image_file, caption="Uploaded Stego-Image", use_container_width=True)

        st.subheader("Message Bit Length")
        message_bit_length_extract = st.number_input(
            "Enter the bit length of the secret message", 
            min_value=1, 
            value=1024, 
            key="lsb_extract_bit_length",
            help="This value is required for extraction and is found in the parameters.json file."
        )
        # 2. Optional Inputs
        st.subheader("Optional Inputs for Metrics")
        col1, col2 = st.columns(2)
        
        with col1:
            optional_cover_image = st.file_uploader("Original Cover Image (for Imperceptibility)", type=["png", "jpg", "bmp"], key="lsb_extract_cover")
        
        with col2:
            optional_original_message = st.text_area("Original Message (for Robustness)", height=155, key="lsb_extract_msg")

        # 3. Extract Button
        st.divider()
        extract_button = st.button("Extract Message", type="primary")

        # 4, 5, 6. Results Section (conditional)
        if extract_button:
            if stego_image_file is None:
                st.error("Please upload a stego-image first!")
            else:
                # --- 4. Extracted Message ---
                st.subheader("Extracted Message")
                st.text_area(
                    "Result", 
                    value="This is the placeholder extracted message...!", 
                    height=100, 
                    disabled=True
                )
                
                # --- 5. Imperceptibility Metrics ---
                st.divider()
                st.subheader("Imperceptibility Metrics")
                if optional_cover_image is not None:
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    metric_col1.metric(label="MSE", value="0.123")
                    metric_col2.metric(label="PSNR (dB)", value="45.67")
                    metric_col3.metric(label="SSIM", value="0.987")
                else:
                    st.info("Upload the original cover image to calculate imperceptibility metrics.")

                # --- 6. Robustness Test ---
                st.divider()
                st.subheader("Robustness Test (Bit Error Ratio - BER)")
                if optional_original_message:
                    
                    # Placeholder for heatmap
                    st.image("https://via.placeholder.com/600x300.png?text=BER+Heatmap+(32+Attacks)", caption="Placeholder for BER Heatmap")
                    
                    # (Alternatively, you could show a table)
                    ber_data = {
                        'Attack': [f'Attack {i+1}' for i in range(32)],
                        'BER': np.random.rand(32) * 0.1 # Dummy data
                    }
                    st.dataframe(pd.DataFrame(ber_data), height=300)
                    
                else:
                    st.info("Enter the original message to calculate robustness (BER).")
        
    elif selected_method == "PVD":
        st.write("This is where the **PVD Extraction** controls will go.")
        # Add PVD-specific extraction widgets here
        st.file_uploader("Upload Stego-Image (PVD)", key="pvd_extract_img")
        st.button("Extract with PVD", key="pvd_extract_btn")

    elif selected_method == "Hybrid (LSB + PVD)":
        st.write("This is where the **Hybrid Extraction** controls will go.")
        # Add Hybrid-specific extraction widgets here
        st.file_uploader("Upload Stego-Image (Hybrid)", key="hybrid_extract_img")
        st.button("Extract with Hybrid", key="hybrid_extract_btn")