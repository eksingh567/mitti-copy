import os
import shutil
import math
from concurrent.futures import ThreadPoolExecutor

def split_dataset(source_dirs, num_batches=5):
    # First, let's establish our 5 target batch directories
    batch_dirs = [f"dataset_batch_{i+1}" for i in range(num_batches)]
    for d in batch_dirs:
        os.makedirs(d, exist_ok=True)
        
    print(f"Distributing images across {num_batches} separate batches...")
    
    # We will gather all images from all source directories (dataset and dataset_new)
    # and map them by class so they stay balanced.
    class_images = {}
    
    for source_dir in source_dirs:
        if not os.path.exists(source_dir):
            continue
            
        classes = os.listdir(source_dir)
        for cls in classes:
            cls_path = os.path.join(source_dir, cls)
            if not os.path.isdir(cls_path):
                continue
                
            if cls not in class_images:
                class_images[cls] = []
                
            images = [os.path.join(cls_path, img) for img in os.listdir(cls_path) if img.lower().endswith(('.png', '.jpg', '.jpeg'))]
            class_images[cls].extend(images)

    def copy_file(src, dst):
        if not os.path.exists(dst):
            shutil.copy2(src, dst)

    total_copied = 0
    
    # For each class, split the total images evenly into the 5 batches
    for cls, images in class_images.items():
        if len(images) == 0:
            continue
            
        batch_size = math.ceil(len(images) / num_batches)
        
        for i, batch_dir in enumerate(batch_dirs):
            os.makedirs(os.path.join(batch_dir, cls), exist_ok=True)
            batch_images = images[i*batch_size : (i+1)*batch_size]
            
            with ThreadPoolExecutor(max_workers=16) as executor:
                for src in batch_images:
                    img_name = os.path.basename(src)
                    dst = os.path.join(batch_dir, cls, img_name)
                    executor.submit(copy_file, src, dst)
            
            total_copied += len(batch_images)
            print(f"Copied {len(batch_images)} images for class '{cls}' into {batch_dir}")

    print(f"Successfully distributed a total of {total_copied} images across {num_batches} batches.")

if __name__ == '__main__':
    # Merge both active datasets
    split_dataset(['dataset', 'dataset_new'], num_batches=5)
