import streamlit as st
import json
import numpy as np
import pandas as pd
from helpers.message_generator import create_pattern_padded_message, DEFAULT_MESSAGE, DEFAULT_TARGET_BIT_SIZE
from methods.spatial.lsb import LSBSteganography, LSB_DEFAULT_PARAM
import cv2 # Diperlukan untuk memproses gambar yang diunggah
from PIL import Image # Diperlukan untuk Image.fromarray
from io import BytesIO



def generate_dummy_message_callback(target_bit_len_key, message_key):
    """
    Fungsi callback yang aman untuk memodifikasi st.session_state 
    yang terikat pada st.text_area.
    """
    dummy_bit_len = st.session_state[target_bit_len_key]
    
    target_byte_size = (dummy_bit_len + 7) // 8 
    
    # 2. Base message sekarang SELALU berasal dari DEFAULT_MESSAGE 
    #    dan di-pad/dipotong hingga ukuran bit/byte target yang ditentukan.
    #    Kita menggunakan DEFAULT_MESSAGE, bukan pesan yang sudah diubah di UI.
    padded_msg = create_pattern_padded_message(DEFAULT_MESSAGE, target_byte_size)
    
    # 3. Set the padded message ke session state
    st.session_state[message_key] = padded_msg
    
    st.toast(f"Message padded to target {dummy_bit_len} bytes ({dummy_bit_len} bits)!")

# --- CONSTANTS ---
METHOD_LSB = "Spatial - LSB"
METHOD_DCT = "Frequency - DCT"
METHOD_HYBRID = "Hybrid - DCT + LSB"
METHODS_ALL = (METHOD_LSB, METHOD_DCT, METHOD_HYBRID)

# Simulasi konstanta DCT dari file eksternal (Pastikan ini sesuai dengan DCT Anda)
DCT_POSITION_MID_LOW = [(1, 1), (2, 0), (0, 2), (3, 0), (0, 3)]
DCT_POSITION_MID = [(2, 1), (1, 2), (2, 2), (3, 1), (1, 3)]
DCT_POSITION_HIGH = [(4, 4), (5, 3), (3, 5), (6, 2), (2, 6)]

# Kamus untuk memetakan nama preset ke data list
DCT_POSITION_PRESETS = {
    "Mid-Low Frequencies": DCT_POSITION_MID_LOW,
    "Mid Frequencies": DCT_POSITION_MID,
    "High Frequencies": DCT_POSITION_HIGH
}
# Daftar nama preset untuk selectbox
DCT_PRESET_NAMES = list(DCT_POSITION_PRESETS.keys())


# --- Sidebar Navigation (FIXED STRUCTURE) ---
st.sidebar.title("Hybrid Steganography 🛡️")
st.sidebar.write("Select your steganography technique:")

# We use headers and text to set up the visual groups,
# then rely on the single radio widget below for selection.
st.sidebar.header("Spatial Domain")
st.sidebar.write(f"• {METHOD_LSB}")

st.sidebar.divider()

st.sidebar.header("Frequency Domain")
st.sidebar.write(f"• {METHOD_DCT}")

st.sidebar.divider()

st.sidebar.header("Hybrid")
st.sidebar.write(f"• {METHOD_HYBRID}")

st.sidebar.divider()

# Single radio control to capture the selection, avoiding duplicate key errors.
selected_method = st.sidebar.radio(
    "Choose Method",
    METHODS_ALL,
    key="final_method_selector", # Unique key
    label_visibility="collapsed"
)


# --- Main Content Area ---
tab_embed, tab_extract = st.tabs(["Embed Message 🖼️", "Extract Message 🕵️"])

# --- Embed Tab Content ---
with tab_embed:
    st.title(f"Embed using {selected_method}")
    
    # --- FLOW LSB ---
    if selected_method == METHOD_LSB:
        
        with st.expander("Configure Parameters"):
            bits_per_channel_embed = st.number_input("Bit Plane (e.g., 1-8)", min_value=1, max_value=8, 
                                                                value=LSB_DEFAULT_PARAM['bits_per_channel'], 
                                                                key="bits_per_channel_embed")
            
        st.subheader("Message Input")
        col1, col2 = st.columns([0.6, 0.4])
            
        with col1:
            lsb_embed_msg = st.text_area(
                "Your Secret Message", 
                height=150, 
                key="lsb_embed_msg", 
                label_visibility="collapsed"
            )
        
        with col2:
            with st.container(border=True):
                st.write("Dummy Message Helper")
                
                dummy_bit_len = st.number_input(
                    "Target Bit Length (must be multiple of 8)", 
                    min_value=8, 
                    value=DEFAULT_TARGET_BIT_SIZE, 
                    step=8, 
                    key="lsb_dummy_bit_len"
                )
                
                st.button(
                    "Generate Dummy Message", 
                    key="lsb_dummy_btn", 
                    on_click=generate_dummy_message_callback,
                    args=("lsb_dummy_bit_len", "lsb_embed_msg") 
                )
        
        st.subheader("Cover Image")
        cover_image_file = st.file_uploader("Upload Cover Image", type=["png", "jpg", "bmp"], key="lsb_embed_img", label_visibility="collapsed")
            
        if cover_image_file is not None:
            # Tampilkan gambar yang diunggah
            st.image(cover_image_file, caption="Uploaded Cover Image", use_container_width=True)
            
        st.divider()
        embed_button = st.button("Embed Message", type="primary", key="lsb_embed_btn")

        if embed_button:
            st.subheader("Embedding Results")
            if cover_image_file is None:
                st.error("Please upload a cover image first!")
            else:
                # --- LOGIKA EMBEDDING NYATA DIMULAI ---
                
                # Membaca file yang diunggah dan mengonversinya ke numpy array (RGB)
                file_bytes = np.asarray(bytearray(cover_image_file.read()), dtype=np.uint8)
                cover_image_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                cover_image_rgb = cv2.cvtColor(cover_image_bgr, cv2.COLOR_BGR2RGB)
                
                # Inisialisasi dan Embed
                try:
                    lsb_stego = LSBSteganography(bits_per_channel=bits_per_channel_embed)
                    stego_image_np, final_bit_length = lsb_stego.embed(cover_image_rgb, lsb_embed_msg)

                    # Konversi numpy array ke objek Image Pillow untuk display/download
                    stego_image_pil = Image.fromarray(stego_image_np)
                    
                    # Konversi Image Pillow ke byte buffer untuk download
 
                    buffer = BytesIO()
                    stego_image_pil.save(buffer, format="PNG")
                    stego_image_bytes = buffer.getvalue()
                    
                    # --- HASIL ---
                    res_col1, res_col2 = st.columns(2)
                    
                    with res_col1:
                        st.write("**Stego-Image**")
                        # Display stego image
                        st.image(stego_image_pil, caption="Steganographic Image", use_container_width=True)
                        
                        st.download_button(
                            label="Download Image",
                            data=stego_image_bytes, 
                            file_name="stego_image.png",
                            mime="image/png"
                        )
                    
                    with res_col2:
                        st.write("**Parameters Used**")
                        # Menggunakan final_bit_length dari hasil embed
                        parameters_to_save = {
                                "method": METHOD_LSB, 
                                "bit_per_channel": bits_per_channel_embed,
                                "message_bit_length": final_bit_length
                        }
                        parameters_json = json.dumps(parameters_to_save, indent=4)
                        
                        st.download_button(
                            label="Download Parameters",
                            data=parameters_json,
                            file_name="parameters.json",
                            mime="application/json"
                        )
                        
                except ValueError as e:
                    st.error(f"Embedding Failed: {e}")
                except Exception as e:
                    st.error(f"An unexpected error occurred during embedding: {e}")
    
    # --- FLOW DCT ---
    elif selected_method == METHOD_DCT:
        
        with st.expander("Configure Parameters"):
            dct_block_size = st.number_input("Block Size", min_value=4, max_value=16, value=8, step=4, key="dct_block_size")
            dct_quant_factor = st.number_input("Quantization Factor", min_value=1, max_value=100, value=70, key="dct_quant_factor")
            
            dct_preset_name = st.selectbox(
                "Embedding Position Preset", 
                options=DCT_PRESET_NAMES, 
                index=1,
                key="dct_embed_pos_preset"
            )
            dct_embed_positions = DCT_POSITION_PRESETS[dct_preset_name]

        st.subheader("Message Input")
        col1, col2 = st.columns([0.6, 0.4]) 

        with col1:
            dct_embed_msg = st.text_area("Your Secret Message", height=150, key="dct_embed_msg", label_visibility="collapsed")
        
        with col2:
            with st.container(border=True):
                st.write("Dummy Message Helper")
                dummy_len = st.number_input("Message Length", min_value=10, value=100, key="dct_dummy_len")
                if st.button("Generate Dummy Message", key="dct_dummy_btn"):
                    st.toast(f"Dummy message of length {dummy_len} generated!")
        
        st.subheader("Cover Image")
        cover_image_file = st.file_uploader("Upload Cover Image", type=["png", "jpg", "bmp"], key="dct_embed_img", label_visibility="collapsed")
            
        if cover_image_file is not None:
            st.image(cover_image_file, caption="Uploaded Cover Image", use_container_width=True)
            
        st.divider()
        embed_button = st.button("Embed Message", type="primary", key="dct_embed_btn")

        if embed_button:
            st.subheader("Embedding Results")
            if cover_image_file is None:
                st.error("Please upload a cover image first!")
            else:
                res_col1, res_col2 = st.columns([0.5, 0.5])
                
                with res_col1:
                    st.write("**Stego-Image**")
                    st.image("https://via.placeholder.com/400x400.png?text=Your+Stego-Image", caption="Steganographic Image", use_container_width=True)
                    st.download_button(
                        label="Download Image",
                        data=b"placeholder_image_data", 
                        file_name="stego_image.png",
                        mime="image/png"
                    )
                
                with res_col2:
                    st.write("**Parameters Used**")
                    message_bit_length = len(dct_embed_msg.encode('utf-8')) * 8
                    parameters_to_save = {
                            "method": METHOD_DCT, 
                            "block_size": dct_block_size,
                            "quant_factor": dct_quant_factor,
                            "embed_positions": dct_embed_positions,
                            "message_bit_length": message_bit_length
                    }
                    parameters_json = json.dumps(parameters_to_save, indent=4)
                    
                    st.download_button(
                        label="Download Parameters",
                        data=parameters_json,
                        file_name="parameters.json",
                        mime="application/json"
                    )

    # --- FLOW HYBRID ---
    elif selected_method == METHOD_HYBRID:
        
        with st.expander("Configure Parameters"):
            hybrid_dct_ratio = st.slider("DCT Ratio", min_value=0.0, max_value=1.0, value=0.5, step=0.1, key="hybrid_ratio")
            st.write(f"**DCT Ratio: {hybrid_dct_ratio*100:.0f}%** | **LSB Ratio: {(1-hybrid_dct_ratio)*100:.0f}%**")
            
            with st.container(border=True):
                st.write("**DCT Parameters**")
                hybrid_quant_factor = st.number_input("Quantization Factor", min_value=1, max_value=100, value=70, key="hybrid_quant_factor")
                
                hybrid_preset_name = st.selectbox(
                    "Embedding Position Preset", 
                    options=DCT_PRESET_NAMES, 
                    index=1,
                    key="hybrid_embed_pos_preset"
                )
                hybrid_embed_positions = DCT_POSITION_PRESETS[hybrid_preset_name]
            
            with st.container(border=True):
                st.write("**LSB Parameters**")
                hybrid_lsb_bits = st.number_input("LSB Bit Plane (e.g., 1-8)", min_value=1, max_value=8, value=1, key="hybrid_lsb_bits")

        st.subheader("Message Input")
        col1, col2 = st.columns([0.6, 0.4]) 

        with col1:
            hybrid_embed_msg = st.text_area("Your Secret Message", height=150, key="hybrid_embed_msg", label_visibility="collapsed")
        
        with col2:
            with st.container(border=True):
                st.write("Dummy Message Helper")
                dummy_len = st.number_input("Message Length", min_value=10, value=100, key="hybrid_dummy_len")
                if st.button("Generate Dummy Message", key="hybrid_dummy_btn"):
                    st.toast(f"Dummy message of length {dummy_len} generated!")
        
        st.subheader("Cover Image")
        cover_image_file = st.file_uploader("Upload Cover Image", type=["png", "jpg", "bmp"], key="hybrid_embed_img", label_visibility="collapsed")
            
        if cover_image_file is not None:
            st.image(cover_image_file, caption="Uploaded Cover Image", use_container_width=True)
            
        st.divider()
        embed_button = st.button("Embed Message", type="primary", key="hybrid_embed_btn")

        if embed_button:
            st.subheader("Embedding Results")
            if cover_image_file is None:
                st.error("Please upload a cover image first!")
            else:
                res_col1, res_col2 = st.columns(2)
                
                with res_col1:
                    st.write("**Stego-Image**")
                    st.image("https://via.placeholder.com/400x400.png?text=Your+Stego-Image", caption="Steganographic Image", use_container_width=True)
                    st.download_button(
                        label="Download Image",
                        data=b"placeholder_image_data", 
                        file_name="stego_image.png",
                        mime="image/png"
                    )
                
                with res_col2:
                    st.write("**Parameters Used**")
                    message_bit_length = len(hybrid_embed_msg.encode('utf-8')) * 8
                    parameters_to_save = {
                        "method": METHOD_HYBRID,
                        "dct_lsb_ratio": (hybrid_dct_ratio, 1.0 - hybrid_dct_ratio),
                        "dct_params": {
                            "quant_factor": hybrid_quant_factor, 
                            "embed_positions": hybrid_embed_positions
                        },
                        "lsb_params": {
                            "bits_per_channel": hybrid_lsb_bits
                        },
                        "message_bit_length": message_bit_length
                    }
                    parameters_json = json.dumps(parameters_to_save, indent=4)
                    
                    st.download_button(
                        label="Download Parameters",
                        data=parameters_json,
                        file_name="parameters.json",
                        mime="application/json"
                    )

# --- Extract Tab Content ---
with tab_extract:
    st.title(f"Extract using {selected_method}")
    
    # --- FLOW LSB ---
    if selected_method == METHOD_LSB:
        
        with st.expander("Configure Parameters"):
            bits_per_channel_extract = st.number_input("LSB Bit Plane (e.g., 1-8)", min_value=1, max_value=8, value=1, key="bits_per_channel_extract")

        st.subheader("Upload Stego-Image")
        stego_image_file = st.file_uploader("Upload the image you want to extract from", type=["png", "jpg", "bmp"], key="lsb_extract_img", label_visibility="collapsed")

        if stego_image_file is not None:
            st.image(stego_image_file, caption="Uploaded Stego-Image", use_container_width=True)

        st.subheader("Message Bit Length")
        message_bit_length_extract = st.number_input(
            "Enter the bit length of the secret message", 
            min_value=1, value=1024, key="lsb_extract_bit_length"
        )
        
        st.subheader("Optional Inputs for Metrics")
        col1, col2 = st.columns(2)
        with col1:
            optional_cover_image = st.file_uploader("Original Cover Image (for Imperceptibility)", type=["png", "jpg", "bmp"], key="lsb_extract_cover")
        with col2:
            optional_original_message = st.text_area("Original Message (for Robustness)", height=155, key="lsb_extract_msg")

        st.divider()
        extract_button = st.button("Extract Message", type="primary", key="lsb_extract_btn")

        if extract_button:
            if stego_image_file is None:
                st.error("Please upload a stego-image first!")
            else:
                st.subheader("Extracted Message")
                st.text_area("Result", value="Placeholder extracted message...!", height=100, disabled=True)
                st.divider()
                st.subheader("Imperceptibility Metrics")
                if optional_cover_image is not None:
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    metric_col1.metric(label="MSE", value="0.123")
                    metric_col2.metric(label="PSNR (dB)", value="45.67")
                    metric_col3.metric(label="SSIM", value="0.987")
                else:
                    st.info("Upload the original cover image to calculate imperceptibility metrics.")
                st.divider()
                st.subheader("Robustness Test (Bit Error Ratio - BER)")
                if optional_original_message:
                    st.image("https://via.placeholder.com/600x300.png?text=BER+Heatmap+(32+Attacks)", caption="Placeholder for BER Heatmap")
                    ber_data = {'Attack': [f'Attack {i+1}' for i in range(32)], 'BER': np.random.rand(32) * 0.1}
                    st.dataframe(pd.DataFrame(ber_data), height=300)
                else:
                    st.info("Enter the original message to calculate robustness (BER).")


    # --- FLOW DCT ---
    elif selected_method == METHOD_DCT:
        
        with st.expander("Configure Parameters"):
            dct_block_size_ext = st.number_input("Block Size", min_value=4, max_value=16, value=8, step=4, key="dct_ext_block_size")
            dct_quant_factor_ext = st.number_input("Quantization Factor", min_value=1, max_value=100, value=70, key="dct_ext_quant_factor")
            
            dct_preset_name_ext = st.selectbox(
                "Embedding Position Preset", 
                options=DCT_PRESET_NAMES, 
                index=1,
                key="dct_ext_embed_pos_preset"
            )
            dct_embed_positions_ext = DCT_POSITION_PRESETS[dct_preset_name_ext]

        st.subheader("Upload Stego-Image")
        stego_image_file = st.file_uploader("Upload the image you want to extract from", type=["png", "jpg", "bmp"], key="dct_extract_img", label_visibility="collapsed")

        if stego_image_file is not None:
            st.image(stego_image_file, caption="Uploaded Stego-Image", use_container_width=True)

        st.subheader("Message Bit Length")
        message_bit_length_extract = st.number_input(
            "Enter the bit length of the secret message", 
            min_value=1, value=1024, key="dct_extract_bit_length"
        )
        
        st.subheader("Optional Inputs for Metrics")
        col1, col2 = st.columns(2)
        with col1:
            optional_cover_image = st.file_uploader("Original Cover Image (for Imperceptibility)", type=["png", "jpg", "bmp"], key="dct_extract_cover")
        with col2:
            optional_original_message = st.text_area("Original Message (for Robustness)", height=155, key="dct_extract_msg")

        st.divider()
        extract_button = st.button("Extract Message", type="primary", key="dct_extract_btn")

        if extract_button:
            if stego_image_file is None:
                st.error("Please upload a stego-image first!")
            else:
                st.subheader("Extracted Message")
                st.text_area("Result", value="Placeholder extracted message...!", height=100, disabled=True)
                st.divider()
                st.subheader("Imperceptibility Metrics")
                if optional_cover_image is not None:
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    metric_col1.metric(label="MSE", value="0.123")
                    metric_col2.metric(label="PSNR (dB)", value="45.67")
                    metric_col3.metric(label="SSIM", value="0.987")
                else:
                    st.info("Upload the original cover image to calculate imperceptibility metrics.")
                st.divider()
                st.subheader("Robustness Test (Bit Error Ratio - BER)")
                if optional_original_message:
                    st.image("https://via.placeholder.com/600x300.png?text=BER+Heatmap+(32+Attacks)", caption="Placeholder for BER Heatmap")
                    ber_data = {'Attack': [f'Attack {i+1}' for i in range(32)], 'BER': np.random.rand(32) * 0.1}
                    st.dataframe(pd.DataFrame(ber_data), height=300)
                else:
                    st.info("Enter the original message to calculate robustness (BER).")


    # --- FLOW HYBRID ---
    elif selected_method == METHOD_HYBRID:
        
        with st.expander("Configure Parameters"):
            hybrid_dct_ratio_ext = st.slider("DCT Ratio", min_value=0.0, max_value=1.0, value=0.5, step=0.1, key="hybrid_ext_ratio")
            st.write(f"**DCT Ratio: {hybrid_dct_ratio_ext*100:.0f}%** | **LSB Ratio: {(1-hybrid_dct_ratio_ext)*100:.0f}%**")
            
            with st.container(border=True):
                st.write("**DCT Parameters**")
                hybrid_quant_factor_ext = st.number_input("Quantization Factor", min_value=1, max_value=100, value=70, key="hybrid_ext_quant_factor")
                
                hybrid_preset_name_ext = st.selectbox(
                    "Embedding Position Preset", 
                    options=DCT_PRESET_NAMES, 
                    index=1,
                    key="hybrid_ext_embed_pos_preset"
                )
                hybrid_embed_positions_ext = DCT_POSITION_PRESETS[hybrid_preset_name_ext]
            
            with st.container(border=True):
                st.write("**LSB Parameters**")
                hybrid_lsb_bits_ext = st.number_input("LSB Bit Plane (e.g., 1-8)", min_value=1, max_value=8, value=1, key="hybrid_ext_lsb_bits")

        st.subheader("Upload Stego-Image")
        stego_image_file = st.file_uploader("Upload the image you want to extract from", type=["png", "jpg", "bmp"], key="hybrid_extract_img", label_visibility="collapsed")

        if stego_image_file is not None:
            st.image(stego_image_file, caption="Uploaded Stego-Image", use_container_width=True)

        st.subheader("Message Bit Length")
        message_bit_length_extract = st.number_input(
            "Enter the bit length of the secret message", 
            min_value=1, value=1024, key="hybrid_extract_bit_length"
        )
        
        st.subheader("Optional Inputs for Metrics")
        col1, col2 = st.columns(2)
        with col1:
            optional_cover_image = st.file_uploader("Original Cover Image (for Imperceptibility)", type=["png", "jpg", "bmp"], key="hybrid_extract_cover")
        with col2:
            optional_original_message = st.text_area("Original Message (for Robustness)", height=155, key="hybrid_extract_msg")

        st.divider()
        extract_button = st.button("Extract Message", type="primary", key="hybrid_extract_btn")

        if extract_button:
            if stego_image_file is None:
                st.error("Please upload a stego-image first!")
            else:
                st.subheader("Extracted Message")
                st.text_area("Result", value="Placeholder extracted message...!", height=100, disabled=True)
                st.divider()
                st.subheader("Imperceptibility Metrics")
                if optional_cover_image is not None:
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    metric_col1.metric(label="MSE", value="0.123")
                    metric_col2.metric(label="PSNR (dB)", value="45.67")
                    metric_col3.metric(label="SSIM", value="0.987")
                else:
                    st.info("Upload the original cover image to calculate imperceptibility metrics.")
                st.divider()
                st.subheader("Robustness Test (Bit Error Ratio - BER)")
                if optional_original_message:
                    st.image("https://via.placeholder.com/600x300.png?text=BER+Heatmap+(32+Attacks)", caption="Placeholder for BER Heatmap")
                    ber_data = {'Attack': [f'Attack {i+1}' for i in range(32)], 'BER': np.random.rand(32) * 0.1}
                    st.dataframe(pd.DataFrame(ber_data), height=300)
                else:
                    st.info("Enter the original message to calculate robustness (BER).")