import kagglehub
import shutil
import os

target_dir = 'raw_datasets'
os.makedirs(target_dir, exist_ok=True)

datasets = [
    ('Rice Leaf Diseases', 'vbookshelf/rice-leaf-diseases', 'rice'),
    ('Coffee Leaf Diseases', 'carlosalombardi/rocole', 'coffee'),
    ('Tea Sickness', 'shibumohapatra/tea-sickness-dataset', 'tea')
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

print("\nAll downloads completed! The raw files are in the 'raw_datasets' folder.")
print("Please review their internal structure and move them into the main 'dataset' folder in the CropName___DiseaseName format.")
