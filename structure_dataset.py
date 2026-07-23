import os
import shutil
import time

source_dirs = ['raw_datasets', 'raw_datasets_infinite', 'dataset_www_scrape', 'dataset_www_scrape_exotic']
target_dir = 'dataset_new'
os.makedirs(target_dir, exist_ok=True)

print("Starting continuous dataset structuring...")

while True:
    moved_count = 0
    for src_dir in source_dirs:
        if not os.path.exists(src_dir):
            continue
            
        for root, dirs, files in os.walk(src_dir):
            folder_name = os.path.basename(root)
            
            # Identify valid class folders (format: CropName___DiseaseName)
            if '___' in folder_name:
                dest_folder = os.path.join(target_dir, folder_name)
                os.makedirs(dest_folder, exist_ok=True)
                
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.JPG', '.JPEG', '.PNG')):
                        src_file = os.path.join(root, file)
                        dst_file = os.path.join(dest_folder, f"{src_dir}_{file}")
                        
                        if not os.path.exists(dst_file):
                            try:
                                shutil.move(src_file, dst_file)
                                moved_count += 1
                            except Exception:
                                pass
                                
    if moved_count > 0:
        print(f"Structured {moved_count} new images into {target_dir}.")
        
    # Wait 60 seconds before checking for newly downloaded files again
    time.sleep(60)
