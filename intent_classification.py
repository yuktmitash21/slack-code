import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def classify_intent(text):
    logging.info(f"Classifying intent for text: {text}")
    # existing code...
    logging.info("Intent classification completed")

if __name__ == "__main__":
    classify_intent("Sample text")