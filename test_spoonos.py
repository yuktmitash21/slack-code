import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_spoonos():
    logging.info("Starting SpoonOS tests")
    # existing code...
    logging.info("SpoonOS tests completed")

if __name__ == "__main__":
    test_spoonos()