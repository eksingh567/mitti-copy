import subprocess
import time

def run_parallel_training(num_batches=5, epochs=30, batch_size=32):
    processes = []
    
    print(f"Starting {num_batches} simultaneous training runs...")
    
    for i in range(num_batches):
        dataset_path = f"dataset_batch_{i+1}"
        model_output = f"model_batch_{i+1}.h5"
        
        cmd = [
            "python", "train_model.py",
            "--dataset", dataset_path,
            "--epochs", str(epochs),
            "--batch_size", str(batch_size),
            "--model_output", model_output
        ]
        
        print(f"Launching Batch {i+1} training...")
        p = subprocess.Popen(cmd)
        
        # Wait for this batch to completely finish before starting the next one (Sequential execution)
        p.wait()
        print(f"Batch {i+1} training completed.")
        
    print("All distributed training runs finished successfully sequentially!")
        
    # Processes are run sequentially above, so we are done here.
        
    print("All distributed training runs finished successfully!")

if __name__ == '__main__':
    # Launch the parallel training sessions
    run_parallel_training(num_batches=5, epochs=30)
