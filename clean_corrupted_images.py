import os
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

def check_image(file_path):
    try:
        with Image.open(file_path) as img:
            img.verify()
        with Image.open(file_path) as img:
            img.load()
    except Exception as e:
        print(f"Deleting corrupted image: {file_path}")
        os.remove(file_path)
        return 1
    return 0

def verify_images(directory):
    print(f"Scanning for corrupted images in {directory} using multi-threading...")
    files_to_check = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.JPG', '.JPEG', '.PNG')):
                files_to_check.append(os.path.join(root, file))
                
    print(f"Found {len(files_to_check)} images to scan. Commencing hyper-scan...")
    
    bad_count = 0
    with ThreadPoolExecutor(max_workers=32) as executor:
        results = executor.map(check_image, files_to_check)
        for res in results:
            bad_count += res
            
    print(f"Scan complete. Deleted {bad_count} corrupted images.")

if __name__ == "__main__":
    verify_images(r"C:\Users\hp\.gemini\antigravity-ide\scratch\mitti\dataset_master")
