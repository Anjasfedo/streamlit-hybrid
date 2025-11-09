import string

def create_pattern_padded_message(base_message: str, target_byte_size: int) -> str:
    """
    Pads a message with a repeating, deterministic pattern of characters
    to reach a specific byte size, cutting the base message if necessary.

    Args:
        base_message (str): The initial message string.
        target_byte_size (int): The desired total size in bytes.

    Returns:
        str: The padded (atau dipotong, jika perlu) message string.
    """
    character_pool = string.ascii_letters + string.digits + string.punctuation

    # 1. Encode the base message to find its current byte size.
    try:
        message_bytes = base_message.encode('utf-8')
    except Exception as e:
        print(f"Error encoding the message: {e}")
        return ""

    current_byte_size = len(message_bytes)
    
    # 2. Check and CUT the base message if too large (PERUBAHAN UTAMA)
    if current_byte_size > target_byte_size:
        # Potong array byte, kemudian dekode kembali string yang valid.
        # Ini akan memotong karakter multi-byte yang tidak lengkap di akhir.
        truncated_bytes = message_bytes[:target_byte_size]
        try:
            truncated_message = truncated_bytes.decode('utf-8', errors='ignore')
            current_byte_size = len(truncated_message.encode('utf-8'))
            base_message = truncated_message
            print(f"⚠️ Warning: Base message was {len(message_bytes)} bytes. It has been truncated to {current_byte_size} bytes (target {target_byte_size}).")
        except Exception:
            # Jika pemotongan byte gagal, kembalikan string kosong
            return ""

    # 3. Calculate the needed padding length.
    padding_needed = target_byte_size - current_byte_size

    # 4. Build the deterministic padding string.
    if padding_needed > 0:
        pattern_repeats = (padding_needed // len(character_pool)) + 1
        full_pattern = character_pool * pattern_repeats
        padding = full_pattern[:padding_needed]
        return base_message + padding
    else:
        # Jika padding needed <= 0, berarti pesan sudah tepat/terpotong tepat ke ukuran target
        return base_message

# --- USAGE EXAMPLE ---
DEFAULT_MESSAGE = (
    "This message uses deterministic padding. 🚀 "
    "The padding is a repeating, non-random sequence. "
    "Let's test it: 123!@#<>? éçñ. 😊👍"
)

DEFAULT_TARGET_BIT_SIZE = 512

# Create the final message using the new function
# SECRET_MESSAGE = create_pattern_padded_message(DEFAULT_MESSAGE, DEFAULT_TARGET_SIZE)
