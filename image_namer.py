import os
import re

# Change this to the path where your images are stored
# Use r"C:\path\to\folder" on Windows
FOLDER_PATH = "./my_images_folder"


def rename_images(folder_path):
    if not os.path.exists(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        return

    # List all files in the directory
    files = os.listdir(folder_path)

    for filename in files:
        # Match 'image' followed by digits and then the extension (e.g., image1.png)
        match = re.match(r"^image(\d+)(\.\w+)$", filename, re.IGNORECASE)

        if match:
            # Extract the number and the file extension
            num_str, ext = match.groups()
            old_num = int(num_str)

            # --- The Pattern Math ---
            # Group every two numbers together (1,2 -> 1; 3,4 -> 2, etc.)
            new_num = (old_num + 1) // 2

            # Alternate between 'a' and 'b' based on odd/even
            new_letter = "a" if old_num % 2 != 0 else "b"

            # Combine them into the new filename
            new_filename = f"{new_num}{new_letter}{ext}"

            # Full paths for renaming
            old_file_path = os.path.join(folder_path, filename)
            new_file_path = os.path.join(folder_path, new_filename)

            # Rename the file
            os.rename(old_file_path, new_file_path)
            print(f"Renamed: {filename} -> {new_filename}")


if __name__ == "__main__":
    rename_images(FOLDER_PATH)