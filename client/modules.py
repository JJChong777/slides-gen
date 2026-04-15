from datetime import datetime
import pytz
import random
import string


API_URL_SLIDE = "http://server_build:3000"


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


LLM_MODEL_MAX_INPUT_LENGTH = 1000  # characters
MAX_ALLOWED_PAGES = 150





