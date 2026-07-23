import os
from PIL import Image
import concurrent.futures
import time
import warnings

# Suppress PIL warnings
warnings.filterwarnings('ignore')

dataset_dir = 'dataset_master'

def check_and_fix_image(filepath):
    try:
        with Image.open(filepath) as img:
            if img.mode != 'RGB':
                # Convert to RGB and overwrite
                rgb_img = img.convert('RGB')
                rgb_img.save(filepath)
                return f"Converted: {filepath}"
    except Exception as e:
        try:
            os.remove(filepath)
            return f"Deleted unreadable: {filepath} ({e})"
        except:
            return f"Failed to delete: {filepath}"
    return None

def main():
    print(f"Scanning {dataset_dir} for non-RGB images...")
    start_time = time.time()
    
    all_files = []
    for root, _, files in os.walk(dataset_dir):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                all_files.append(os.path.join(root, f))
                
    total_files = len(all_files)
    print(f"Found {total_files} images. Checking color modes with 32 threads...")
    
    converted = 0
    deleted = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
        results = executor.map(check_and_fix_image, all_files)
        
        for i, res in enumerate(results):
            if res:
                if "Converted" in res:
                    converted += 1
                elif "Deleted" in res:
                    deleted += 1
                print(res)
            
            if (i + 1) % 50000 == 0:
                print(f"Processed {i + 1}/{total_files}...")

    print(f"Done in {time.time() - start_time:.2f} seconds.")
    print(f"Converted {converted} images to pure RGB.")
    print(f"Deleted {deleted} completely broken images.")

if __name__ == '__main__':
    main()
