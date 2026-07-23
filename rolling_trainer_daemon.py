import os
import shutil
import time
import subprocess
import glob

def get_all_images(source_dirs):
    images = []
    for d in source_dirs:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    images.append(os.path.join(root, file))
    return images

def build_batch(batch_dir, source_dirs, target_size=100000):
    images = get_all_images(source_dirs)
    if len(images) < target_size:
        return False
        
    print(f"Pool has {len(images)} images. Moving {target_size} into {batch_dir}...")
    os.makedirs(batch_dir, exist_ok=True)
    
    # We want to maintain class structure
    moved = 0
    for img_path in images[:target_size]:
        class_name = os.path.basename(os.path.dirname(img_path))
        target_class_dir = os.path.join(batch_dir, class_name)
        os.makedirs(target_class_dir, exist_ok=True)
        
        target_path = os.path.join(target_class_dir, os.path.basename(img_path))
        shutil.move(img_path, target_path)
        moved += 1
        if moved % 10000 == 0:
            print(f"Moved {moved}/{target_size} images...")
            
    print(f"Successfully built {batch_dir} with {moved} images.")
    return True

def run_daemon():
    num_batches = 5
    epochs = 30
    batch_size = 32
    source_dirs = ['dataset', 'dataset_new']
    
    print("Starting Continuous Rolling Trainer Daemon...")
    
    for i in range(1, num_batches + 1):
        batch_dir = f"dataset_batch_{i}"
        model_output = f"model_batch_{i}.h5"
        
        # Check if model already exists (meaning it's done)
        if os.path.exists(model_output):
            print(f"{model_output} already exists. Skipping batch {i}.")
            continue
            
        print(f"\n--- Preparing Batch {i} ---")
        
        # Wait until we can build the batch
        while True:
            # Check if batch dir already has enough images (in case daemon crashed and restarted)
            existing = len(get_all_images([batch_dir]))
            if existing >= 99000: # Allow slight variance
                print(f"{batch_dir} already built.")
                break
                
            success = build_batch(batch_dir, source_dirs, target_size=100000)
            if success:
                break
                
            available = len(get_all_images(source_dirs))
            print(f"Only {available}/100000 images available for batch {i}. Waiting 5 minutes...")
            time.sleep(300)
            
        print(f"Starting 30-epoch training for Batch {i}...")
        cmd = [
            "python", "train_model.py",
            "--dataset", batch_dir,
            "--epochs", str(epochs),
            "--batch_size", str(batch_size),
            "--model_output", model_output
        ]
        
        if i > 1:
            prev_model = f"model_batch_{i-1}.h5"
            if os.path.exists(prev_model):
                cmd.extend(["--initial_weights", prev_model])
                print(f"Loading weights from {prev_model} to continue training!")
        
        # Run sequentially (blocks until finished). Will raise exception if it crashes.
        subprocess.run(cmd, check=True)
        print(f"Batch {i} 30-epoch training finished! Saved {model_output}.")
        
    print("\nAll 5 batches finished! Merging models...")
    subprocess.run(["python", "merge_models.py"])
    print("Daemon finished successfully!")

if __name__ == '__main__':
    run_daemon()
