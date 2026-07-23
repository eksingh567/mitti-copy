import os
import argparse
from PIL import Image
import multiprocessing

def check_image(filepath):
    try:
        with Image.open(filepath) as img:
            img.verify()  # verify that it is, in fact, an image
        return None
    except Exception as e:
        return filepath

def clean_directory(directory_path):
    print(f"Scanning {directory_path} for corrupted images...")
    
    all_files = []
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                all_files.append(os.path.join(root, file))
                
    print(f"Found {len(all_files)} images. Starting verification (this may take a while)...")
    
    # Use multiprocessing to speed up the scanning of 490k images
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    corrupted_files = pool.map(check_image, all_files)
    pool.close()
    pool.join()
    
    # Filter out None values
    corrupted_files = [f for f in corrupted_files if f is not None]
    
    print(f"Found {len(corrupted_files)} corrupted images.")
    
    if len(corrupted_files) > 0:
        print("Deleting corrupted images...")
        for file in corrupted_files:
            try:
                os.remove(file)
            except Exception as e:
                print(f"Failed to delete {file}: {e}")
        print("Deletion complete.")
    else:
        print("Dataset is clean!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Clean corrupted images from a dataset directory")
    parser.add_argument('--dataset', type=str, default='dataset_master', help='Path to the dataset directory')
    args = parser.parse_args()
    
    clean_directory(args.dataset)
