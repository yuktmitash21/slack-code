import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_spoonos(version):
    logging.info(f"Searching for SpoonOS version: {version}")
    # existing code...
    logging.info(f"SpoonOS version {version} found")

if __name__ == "__main__":
    find_spoonos("1.0")