import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def github_operation():
    logging.info("Starting GitHub operation")
    # existing code...
    logging.info("GitHub operation completed")

if __name__ == "__main__":
    github_operation()