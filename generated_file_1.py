import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_file():
    logging.info("Generating file")
    # existing code...
    logging.info("File generation completed")

if __name__ == "__main__":
    generate_file()