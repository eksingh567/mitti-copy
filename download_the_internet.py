import os
import subprocess
import json
import shutil
import time

target_dir = 'raw_datasets_infinite'
os.makedirs(target_dir, exist_ok=True)

queries = ['crop disease', 'plant disease', 'leaf disease', 'agriculture disease', 'farm disease']
all_datasets = set()

print("Searching Kaggle's entire database for anything related to crop diseases...")

for query in queries:
    print(f"Searching query: '{query}'...")
    # We ask for up to 20 results per query to get the top 100 datasets total
    cmd = ['kaggle', 'datasets', 'list', '-s', query, '--json']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        try:
            # The Kaggle CLI output might have some warnings before the JSON, we find the first '['
            stdout = result.stdout
            json_start = stdout.find('[')
            if json_start != -1:
                datasets = json.loads(stdout[json_start:])
                for d in datasets:
                    all_datasets.add(d['ref'])
        except Exception as e:
            pass
            
print(f"\nBOOM! Found {len(all_datasets)} unique datasets across Kaggle!")
print("Starting the mass download process...")

for idx, dataset_id in enumerate(list(all_datasets)):
    print(f"\n[{idx+1}/{len(all_datasets)}] Downloading {dataset_id}...")
    folder_name = dataset_id.replace('/', '_')
    dest = os.path.join(target_dir, folder_name)
    
    if os.path.exists(dest):
        print("Already downloaded. Skipping.")
        continue
        
    try:
        # Download using the Kaggle CLI
        subprocess.run(['kaggle', 'datasets', 'download', '-d', dataset_id, '-p', dest, '--unzip'], check=True)
        print(f"Successfully downloaded and unzipped {dataset_id}")
    except Exception as e:
        print(f"Error downloading {dataset_id}: {e}")
        
print("\n=======================================================================")
print("THE 'ONE AND ONLY' COLLECTION IS COMPLETE!")
print(f"All files have been sucked down into the '{target_dir}' folder.")
print("=======================================================================")
