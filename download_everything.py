import kagglehub
import shutil
import os

target_dir = 'raw_datasets'
os.makedirs(target_dir, exist_ok=True)

# A massive list of every major plant/crop disease dataset available on Kaggle
datasets = [
    ('PlantVillage Original', 'emmarex/plantdisease', 'plantvillage'),
    ('PlantDoc (Real World Backgrounds)', 'pratik2901/plantdoc', 'plantdoc'),
    ('New Plant Diseases Dataset', 'vipoooool/new-plant-diseases-dataset', 'new_plant_diseases'),
    ('Tomato Diseases', 'noulam/tomato', 'tomato'),
    ('Plant Disease Recognition', 'rashikrahmanpritom/plant-disease-recognition-dataset', 'plant_disease_recognition'),
    ('Merged Plant Disease Dataset', 'nafinm/plant-disease-classification-merged-dataset', 'merged_plant_disease'),
    ('Plant Pathology 2020', 'c/plant-pathology-2020-fgvc7', 'apple_2020'), 
    ('Cassava Leaf Disease', 'c/cassava-leaf-disease-classification', 'cassava'),
    ('Maize (Corn) Disease', 'smaranjitghose/corn-or-maize-leaf-disease-dataset', 'maize'),
    ('Potato Disease', 'arjuntejaswi/plant-village', 'potato_and_others'),
    ('Soybean Disease', 'akashkrishanan/soybean-disease-dataset', 'soybean')
]

print("Starting the Ultimate Dataset Aggregator...")
print("Fetching 11 massive datasets. This will take a while, but it will be worth it!\n")

for name, kaggle_id, folder_name in datasets:
    print(f"\n--- Fetching {name} ---")
    try:
        # Check if it's a competition or standard dataset based on prefix
        if kaggle_id.startswith('c/'):
            comp_id = kaggle_id.replace('c/', '')
            path = kagglehub.competition_download(comp_id)
        else:
            path = kagglehub.dataset_download(kaggle_id)
            
        print(f"Downloaded securely to cache: {path}")
        
        dest = os.path.join(target_dir, folder_name)
        if not os.path.exists(dest):
            print(f"Copying files to {dest}... (Please be patient, these are huge)")
            shutil.copytree(path, dest)
            print("Done copying.")
        else:
            print(f"Folder {dest} already exists! Skipping to save time.")
            
    except Exception as e:
        print(f"Error downloading {name}: {e}")
        if '403' in str(e):
            print(" -> Make sure to accept the competition rules on Kaggle for this specific dataset.")

print("\n=======================================================")
print("MASSIVE DOWNLOADS COMPLETED! All files are in 'raw_datasets'.")
print("=======================================================")
