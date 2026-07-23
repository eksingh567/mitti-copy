import zipfile
import os

source_dir = r"C:\Users\hp\Downloads\raw"
target_dir = r"C:\Users\hp\.gemini\antigravity-ide\scratch\mitti\raw_datasets_infinite"

print("INITIATING CUSTOM ARCHIVE EXTRACTION")
for f in os.listdir(source_dir):
    if f.endswith('.zip'):
        zip_path = os.path.join(source_dir, f)
        # Create a unique folder for each archive
        extract_folder = os.path.join(target_dir, "custom_" + f.replace('.zip', '').replace(' ', '_').replace('(', '').replace(')', ''))
        os.makedirs(extract_folder, exist_ok=True)
        print(f"Extracting {f} into {extract_folder}...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_folder)
            print(f"Success: {f}")
        except Exception as e:
            print(f"Failed to extract {f}: {e}")

print("==========================================")
print("CUSTOM ARCHIVES SUCCESSFULLY MERGED INTO PIPELINE")
print("==========================================")
