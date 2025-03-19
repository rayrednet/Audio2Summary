import logging
import os

# Ensure logs directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
EVAL_LOG_DIR = os.path.join(LOG_DIR, "evaluations")
os.makedirs(EVAL_LOG_DIR, exist_ok=True)

# Define log file path
LOG_FILE = os.path.join(LOG_DIR, "momify.log")
EVAL_LOG_FILE = os.path.join(EVAL_LOG_DIR, "evaluation.log")

# Create a list to store logs for UI
log_messages = []

# Custom logging handler to capture logs in memory for UI display
class StreamlitLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        log_messages.append(log_entry)  # Store logs in a list

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),  # Save to file
        logging.StreamHandler(),  # Print to console
        StreamlitLogHandler()  # Capture logs for UI
    ]
)

# Create a logger instance
logger = logging.getLogger("MoMify")

# ✅ Configure Evaluation Logger (Metrics & Performance)
eval_logger = logging.getLogger("EvaluationLogger")
eval_handler = logging.FileHandler(EVAL_LOG_FILE, encoding="utf-8")
eval_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
eval_handler.setFormatter(eval_formatter)
eval_logger.addHandler(eval_handler)
eval_logger.setLevel(logging.INFO)


# ✅ **Function to Handle System Errors and Provide Suggestions**
def handle_system_error(error_message):
    """
    Handles system errors by logging them, providing a formatted error message, and suggesting solutions.

    Args:
        error_message (str): The error description.
    """
    log_entry = f"❌ Error encountered: {error_message}"
    logger.error(log_entry)

    # ✅ Error handling suggestions
    if "file format" in error_message.lower():
        suggestion = "🔹 Suggestion: Please upload a supported audio or video file (MP3, WAV, MP4, etc.)."

    elif "file size" in error_message.lower():
        suggestion = "🔹 Suggestion: Try compressing the file or selecting a smaller file (Max: 1GB)."

    elif "no audio" in error_message.lower():
        suggestion = "🔹 Suggestion: Ensure the video contains an audio track before uploading."

    elif "network" in error_message.lower() or "connection" in error_message.lower():
        suggestion = "🔹 Suggestion: Check your internet connection and try again."

    elif "gpu" in error_message.lower():
        suggestion = "🔹 Suggestion: No GPU detected. Running on CPU, which may be slower."

    else:
        suggestion = "🔹 Suggestion: Please check the error log for more details."

    logger.warning(suggestion)
