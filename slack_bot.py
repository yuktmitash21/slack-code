import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def start_slack_bot():
    logging.info("Starting Slack bot")
    # existing code...
    logging.info("Slack bot finished")

if __name__ == "__main__":
    start_slack_bot()