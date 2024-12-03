import os
import csv
from shutil import copyfile

# Step 1: Set paths
dataset_path = "../uploads/portrait_dataset"  # Path to the downloaded dataset folder
output_folder = "../uploads/profile_photos"  # Path where renamed photos will be saved
user_csv = "../data/User1.csv"  # Generated users CSV

# Step 2: Rename images
def rename_images(num_users):
    images = sorted("../uploads/portrait_dataset")  # Sort to ensure consistent mapping
    if len(images) < num_users:
        raise ValueError("Not enough images in the dataset to match the number of users.")

    for uid in range(num_users):
        src = os.path.join(dataset_path, images[uid])
        dest = os.path.join(output_folder, f"user_{uid}.jpg")
        copyfile(src, dest)
    print(f"Renamed {num_users} images and saved to {output_folder}")

# Step 3: Update User1.csv to include profile photo paths
def update_user_csv():
    users = []
    with open(user_csv, 'r') as infile:
        reader = csv.reader(infile)
        for row in reader:
            uid = int(row[0])  # User ID
            profile_photo = f"/profile_photos/user_{uid}.jpg"
            row.append(profile_photo)
            users.append(row)

    with open(user_csv, 'w') as outfile:
        writer = csv.writer(outfile, dialect='unix')
        writer.writerows(users)
    print(f"Updated {user_csv} with profile photo paths")

# Main execution
num_users = 30
print(len(sorted("../uploads/portrait_dataset")))
rename_images(num_users)
update_user_csv()
