import os
import shutil

source_dirs = ['dataset', 'dataset_new', 'dataset_batch_1', 'dataset_batch_2', 'raw_datasets', 'raw_datasets_infinite', 'dataset_www_scrape', 'dataset_www_scrape_exotic']
target_dir = 'dataset_master'
os.makedirs(target_dir, exist_ok=True)

print("Starting high-speed consolidation (Move instead of Copy)...")
moved_count = 0

for src_dir in source_dirs:
    if not os.path.exists(src_dir):
        continue
        
    print(f"Scanning {src_dir}...")
    for root, dirs, files in os.walk(src_dir):
        folder_name = os.path.basename(root)
        
        # Determine class name. For structured ones it's folder_name
        dest_folder = os.path.join(target_dir, folder_name)
        
        image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.JPG', '.JPEG', '.PNG'))]
        if not image_files:
            continue
            
        # Ensure we don't accidentally dump images into the root of dataset_master
        if root == src_dir:
             # Images right at the root of a dataset folder shouldn't happen, but just in case
             dest_folder = os.path.join(target_dir, "Unknown_Class")
             
        os.makedirs(dest_folder, exist_ok=True)
        
        for file in image_files:
            src_file = os.path.join(root, file)
            # Use src_dir prefix to avoid file name collisions
            unique_name = f"{src_dir}_{file}"
            dst_file = os.path.join(dest_folder, unique_name)
            
            if not os.path.exists(dst_file):
                try:
                    shutil.move(src_file, dst_file)
                    moved_count += 1
                except Exception as e:
                    pass
                    
    print(f"Finished moving files from {src_dir}")

print(f"Successfully consolidated {moved_count} images into {target_dir}!")
