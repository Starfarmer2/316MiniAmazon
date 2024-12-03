import os
import random
import shutil

# Function to shuffle and rename image files
def shuffle_rename_images(folder_path):
    # List all image files in the folder
    files = [f for f in os.listdir(folder_path) if f.endswith(".jpg")]

    # Generate a random shuffle of numbers from 0 to 200
    shuffled_numbers = list(range(201))
    # print(shuffled_numbers)
    random.shuffle(shuffled_numbers)
    # print(shuffled_numbers)

    # Loop through the files and rename them
    for old_name, new_number in zip(files, shuffled_numbers):
        print(old_name, new_number)
        # Construct the new name with the format 'product_x.jpg'
        new_name = f"product_{new_number}.jpg"

        # Get the full paths for the old and new files
        old_file = os.path.join(folder_path, old_name)
        new_file = os.path.join(folder_path+'/shuffled', new_name)

        shutil.copy(old_file, new_file)
        # Rename the file
        # os.rename(old_file, new_file)
        print(f"Renamed: {old_name} -> {new_name}")

# Input values
folder_path = "/home/ubuntu/316MiniAmazon/db/uploads/images"  # Replace with your actual folder path

# Call the function to shuffle and rename images
shuffle_rename_images(folder_path)
