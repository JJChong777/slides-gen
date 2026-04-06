import streamlit as st
import requests
from io import BytesIO

from datetime import datetime
import pytz
import random
import string
from enum import Enum

# slide deck AI
# from pypdf import PdfReader

##########################################
## SEARCH, GENERATION AND EDIT HELPERS ###
##########################################

# Define desired thumbnail size
THUMBNAIL_SIZE = (200, 150) # Width, Height
API_URL_SLIDE = "http://slidebuild:3000"

class RequestType(str, Enum):
    GET = "GET"
    POST = "POST"

def make_safe_request(req_type: RequestType, url: str, payload: dict = None) -> tuple[bool, bytes | str]:
    try:
        if req_type == RequestType.GET:
            # For GET, payload goes into params
            response = requests.get(url, params=payload)
        elif req_type == RequestType.POST:
            # For POST, payload goes into json body
            response = requests.post(url, data=payload)
        response.raise_for_status()
        return True, response
    except requests.exceptions.HTTPError as http_err:
        error_msg = f"HTTP error occurred: {http_err}"
        # Check if a response object exists before accessing its attributes
        if http_err.response is not None:
            if http_err.response.status_code is not None: # status_code itself can be None in some edge cases
                error_msg += f", Status Code: {http_err.response.status_code}"
            # Use http_err.response.text to get the body content, not just http_err.response itself
            if http_err.response.text: # Check if response_text is not empty
                error_msg += f", Response Text: {http_err.response.text}"
        return False, error_msg
    except requests.exceptions.ConnectionError:
        return False, "Connection error. Is the server running or URL correct?"
        
    except requests.exceptions.Timeout:
        return False, "Timeout error: The request took too long."
    except requests.exceptions.RequestException as err:
        return False, f"An unexpected request error occurred: {err}"
    except Exception as e:
        return False, f"An unexpected error occurred: {e}"


def generate_file_name():
    # Singapore time
    sg_tz = pytz.timezone("Asia/Singapore")
    now = datetime.now(sg_tz)

    # Format: YYYYMMDD_HHMMSS
    timestamp = now.strftime("%Y%m%d_%H%M%S")

    # 4-char random hash
    random_hash = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

    # Final filename
    filename = f"{timestamp}_{random_hash}"
    return filename

def display_img_with_download(img_bytes, name):
    try:
        # Check if img_bytes is actually valid image data
        if not img_bytes:
            st.error("No image data received")
            return
        
        # Try to validate the image data
        try:
            # Test if it's valid image data
            test_image = Image.open(BytesIO(img_bytes))
            test_image.verify()  # Verify it's a valid image
        except Exception as e:
            st.error(f"Invalid image data: {str(e)}")
            st.error("The response from the server is not a valid image")
            # Debug: show first 100 characters of the response
            if isinstance(img_bytes, bytes):
                st.error(f"Response starts with: {img_bytes[:100]}")
            return
        
        # Reset BytesIO position after verify()
        img_io = BytesIO(img_bytes)
        
        # Display the image
        st.image(img_io, caption=name, width=500)
        
        # Add download button
        st.download_button(
            label=f"Download {name}",
            data=img_bytes,
            file_name=f"{name}.png",
            mime="image/png"
        )
        
    except Exception as e:
        st.error(f"Error displaying image: {str(e)}")
        # Show debug info
        st.error(f"Image bytes type: {type(img_bytes)}")
        if hasattr(img_bytes, '__len__'):
            st.error(f"Image bytes length: {len(img_bytes)}")
        # Show first 200 characters if it's text/HTML error response
        if isinstance(img_bytes, bytes):
            try:
                preview = img_bytes[:200].decode('utf-8', errors='ignore')
                st.error(f"Response preview: {preview}")
            except:
                st.error("Could not decode response as text")

def process_image_bytes_to_thumbnail(image_bytes: bytes, name: str) -> bytes | None:
    """
    Accepts raw image bytes and processes them into a fixed-size thumbnail.

    Args:
        image_bytes (bytes): The raw image data in bytes.
        name (str): The name associated with the image (for display/file naming).

    Returns:
        tuple[bytes | None, str]: A tuple containing the processed image bytes (or None on error)
                                  and the original name.
    """
    if not image_bytes:
        st.warning(f"No image bytes provided for {name}.")
        return None

    try:
        # 1. Load the image from bytes using io.BytesIO and PIL.Image.open
        # Ensure it's in a format PIL can read (e.g., JPEG, PNG)
        img = Image.open(BytesIO(image_bytes))

        # Ensure the image is in RGB mode, especially for certain operations or if saving as JPEG
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # 2. Create a thumbnail with a fixed size (Option 1: Resize and crop to fill)
        processed_img = ImageOps.fit(img, THUMBNAIL_SIZE, Image.LANCZOS)

        # 3. Convert the processed image back to bytes
        byte_arr = BytesIO()
        processed_img.save(byte_arr, format='JPEG') # Save as JPEG for common use
        return byte_arr.getvalue()
    except Exception as e:
        st.error(f"Error processing image {name}: {e}")
        return None

def display_img_with_download_thumbnail(image_data, name):
    thumbnail_img_bytes= process_image_bytes_to_thumbnail(image_data, name)
    if image_data:
        # Create a thumbnail-style card layout
        with st.container():
            with st.columns([1, 4, 1])[1]:  # Center column
                st.image(thumbnail_img_bytes, caption=name, use_container_width=True)  # Thumbnail size
                st.download_button(
                    label=f"Download {name}",
                    data=image_data,
                    file_name=f"{name.replace(' ', '_')}.jpg",
                    mime="image/jpeg",
                    key=f"download_{name}",
                    on_click="ignore"
                )

def toggle_debug_mode(debug_on: bool, api_url: str):
    """Call FastAPI endpoints to toggle debug mode"""
    try:
        if debug_on:
            response = requests.get(f"{api_url}/debug_on")
        else:
            response = requests.get(f"{api_url}/debug_off")
        
        if response.status_code == 200:
            return True, f"Debug mode {'ON' if debug_on else 'OFF'}"
        else:
            return False, f"Error: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"

def debug_mode_checkbox(page: str):
    # Ensure session state key exists
    debug_key = f"debug_mode_{page.lower()}"
    if debug_key not in st.session_state:
        st.session_state[debug_key] = False
    
    # App header with debug checkbox
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.title(f"Generative Design App: {page}")
        
        with col2:
            # Debug mode toggle - directly use session state
            debug_mode = st.checkbox(
                f"Debug Mode {page}", 
                value=st.session_state[debug_key],
                help=f"Reduces inference steps {page} for faster debugging",
                key=f"debug_checkbox_{page.lower()}"
            )
            
            # Update session state and call API when checkbox changes
            if debug_mode != st.session_state[debug_key]:
                st.session_state[debug_key] = debug_mode
                
                with st.spinner("Updating debug mode..."):
                    success, message = toggle_debug_mode(debug_mode, page_to_API_URL[page])
                    
                    if success:
                        if debug_mode:
                            st.success("Debug mode ON - Fast inference enabled")
                        else:
                            st.success("Debug mode OFF - Quality inference enabled")
                    else:
                        st.error(f"Failed to update debug mode: {message}. Refresh the page.")
                        # Revert session state on failure
                        st.session_state[debug_key] = not debug_mode
    
    # Optional status indicator
    if st.session_state[debug_key]:
        st.info("Debug Mode Active - Using fast inference settings")
    
    st.divider()

#########################################
## SLIDE DECK AI HELPERS AND CONSTANTS ##
#########################################
### get PPTX template names and captions
PPTX_TEMPLATE_FILES = {
    'Basic': {
        'caption': 'A good start'
    },
    'Ion Boardroom': {
        'caption': 'Make some bold decisions'
    },
    'Minimalist Sales Pitch': {
        'caption': 'In high contrast'
    },
    'Urban Monochrome': {
        'caption': 'Marvel in a monochrome dream'
    },
}

LLM_MODEL_MAX_INPUT_LENGTH = 1000  # characters
MAX_ALLOWED_PAGES = 150





