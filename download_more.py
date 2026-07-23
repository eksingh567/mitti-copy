import kagglehub
import shutil
import os

target_dir = 'raw_datasets'
os.makedirs(target_dir, exist_ok=True)

datasets = [
    ('Cotton Disease', 'janmejaybhoi/cotton-disease-dataset', 'cotton'),
    ('Sugarcane Leaf Disease', 'nirmalsankalana/sugarcane-leaf-disease-dataset', 'sugarcane'),
    ('Wheat Leaf Rust', 'sadikaljarif/wheat-leaf-rust-dataset', 'wheat_rust'),
    ('Grapevine Leaves', 'muratkokludataset/grapevine-leaves-image-dataset', 'grape')
]

for name, kaggle_id, folder_name in datasets:
    print(f"\n--- Downloading {name} ---")
    try:
        path = kagglehub.dataset_download(kaggle_id)
        print(f"Successfully downloaded to Kaggle cache: {path}")
        
        dest = os.path.join(target_dir, folder_name)
        if not os.path.exists(dest):
            print(f"Copying files to {dest}...")
            shutil.copytree(path, dest)
            print("Done copying.")
        else:
            print(f"Folder {dest} already exists.")
            
    except Exception as e:
        print(f"Error downloading {name}: {e}")

print("\nExtra downloads completed! Check the 'raw_datasets' folder.")
