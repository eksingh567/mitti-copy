import os
from PIL import Image
import concurrent.futures
import time

# Strictly fail on truncated images
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = False

dataset_dir = 'dataset_master'

def check_and_delete_if_corrupt(filepath):
    try:
        # We must call load() to force PIL to read the actual pixel data.
        # img.verify() only reads the header, which is why the last script missed this!
        with Image.open(filepath) as img:
            img.load()
    except Exception as e:
        try:
            os.remove(filepath)
            return f"Deleted truncated/corrupt: {filepath} ({e})"
        except:
            return f"Failed to delete: {filepath}"
    return None

def main():
    print(f"Deep scanning {dataset_dir} for truncated JPEGs...")
    start_time = time.time()
    
    all_files = []
    for root, _, files in os.walk(dataset_dir):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                all_files.append(os.path.join(root, f))
                
    total_files = len(all_files)
    print(f"Found {total_files} images. Forcing full pixel decode with 32 threads...")
    
    deleted = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
        results = executor.map(check_and_delete_if_corrupt, all_files)
        
        for i, res in enumerate(results):
            if res:
                deleted += 1
                print(res)
            
            if (i + 1) % 50000 == 0:
                print(f"Processed {i + 1}/{total_files}...")

    print(f"Done in {time.time() - start_time:.2f} seconds.")
    print(f"Deleted {deleted} completely broken/truncated images.")

if __name__ == '__main__':
    main()
