import logging
import os

# Ensure logs directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Define log file path
LOG_FILE = os.path.join(LOG_DIR, "momify.log")

# Create a list to store logs for UI
log_messages = []

# Custom logging handler to capture logs in memory for UI display
class StreamlitLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        log_messages.append(log_entry)  # Store logs in a list

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more details
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),  # Save to file
        logging.StreamHandler(),  # Print to console
        StreamlitLogHandler()  # Capture logs for UI
    ]
)

# Create a logger instance
logger = logging.getLogger("MoMify")
