import os
import shutil

# Path to the repository directory
directory_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Function to delete all files and directories within the specified path
def delete_all_contents(path):
    try:
        # Iterate over all the files and directories in the given path
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            # Check if it is a file or directory and remove it
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)  # Remove the file or link
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)  # Remove the directory and its contents
        print(f"All contents deleted from {path}")
    except Exception as e:
        print(f"Error occurred while deleting contents: {e}")

# Execute the deletion
delete_all_contents(directory_path)