import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def connect_to_spoonos():
    logging.info("Connecting to SpoonOS")
    # existing code...
    logging.info("Connected to SpoonOS")

if __name__ == "__main__":
    connect_to_spoonos()