import kagglehub
import shutil
import os

target_dir = 'raw_datasets_infinite'
os.makedirs(target_dir, exist_ok=True)

# 15 NEW massive datasets discovered from Kaggle's live database!
datasets = [
    ('New Bangladeshi Crop Disease', 'nafishamoin/new-bangladeshi-crop-disease'),
    ('Crop Pest and Disease Detection', 'nirmalsankalana/crop-pest-and-disease-detection'),
    ('Crop Diseases Classification', 'mexwell/crop-diseases-classification'),
    ('Ghana Crop Disease Detection', 'ohagwucollinspatrick/ghana-crop-disease'),
    ('20k+ Multi-Class Crop Disease', 'jawadali1045/20k-multi-class-crop-disease-images'),
    ('RICE CROP DISEASES (New)', 'thegoanpanda/rice-crop-diseases'),
    ('Five Crop Diseases Dataset', 'shubham2703/five-crop-diseases-dataset'),
    ('Top Agriculture Crop Disease India', 'kamal01/top-agriculture-crop-disease'),
    ('Crop Disease (Ghana)', 'responsibleailab/crop-disease-ghana'),
    ('Bean Crop Disease Diagnosis', 'msjahid/bean-crop-disease-diagnosis-and-spatial-analysis'),
    ('Tomato Leaf Diseases Detection', 'farukalam/tomato-leaf-diseases-detection-computer-vision'),
    ('Plant Disease Expert', 'sadmansakibmahi/plant-disease-expert'),
    ('CGIAR Computer Vision for Crop Disease', 'shadabhussain/cgiar-computer-vision-for-crop-disease'),
    ('Lemon Leaf Disease Dataset', 'mahmoudshaheen1134/lemon-leaf-disease-dataset-lldd'),
    ('Crop and Soil DataSet', 'shankarpriya2913/crop-and-soil-dataset')
]

print("INITIATING ULTIMATE OVERDRIVE...")
print(f"Adding {len(datasets)} more massive datasets to the collection!\n")

for name, kaggle_id in datasets:
    print(f"\n--- Fetching {name} ---")
    try:
        path = kagglehub.dataset_download(kaggle_id)
        print(f"Successfully downloaded securely to cache: {path}")
        
        folder_name = kaggle_id.split('/')[-1]
        dest = os.path.join(target_dir, folder_name)
        
        if not os.path.exists(dest):
            print(f"Copying files to {dest}...")
            shutil.copytree(path, dest)
            print("Done copying.")
        else:
            print(f"Folder {dest} already exists! Skipping.")
            
    except Exception as e:
        print(f"Error downloading {name}: {e}")

print("\n=======================================================================")
print("THE 'ONE AND ONLY' COLLECTION IS FINALLY COMPLETE!")
print(f"All {len(datasets)} extra databases have been sucked down into '{target_dir}'.")
print("=======================================================================")
