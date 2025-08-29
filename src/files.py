

import base64
import os

def serialize_to_base64(filename: str):
    """
    Produce a base64-encoded string of the file at `filename`.

    Errors if the file is greater than 20MB (Gemini max size for base64 uploads.)

    Note: Gemini intends for this to be used for PDFs, but we won't enforce that.
    """
    # Check if file exists
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")
    
    # Check file size (20MB limit)
    file_size = os.path.getsize(filename)
    max_size = 20 * 1024 * 1024  # 20MB in bytes
    if file_size > max_size:
        raise ValueError(f"File size {file_size} bytes exceeds 20MB limit ({max_size} bytes)")
    
    # Read and encode the file
    with open(filename, 'rb') as file:
        file_content = file.read()
        base64_content = base64.b64encode(file_content).decode('utf-8')
    
    return base64_content