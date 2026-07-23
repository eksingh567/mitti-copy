import kagglehub
import sys

def download_dataset():
    print("Downloading Plant Pathology 2021 dataset...")
    try:
        path = kagglehub.competition_download('plant-pathology-2021-fgvc8')
        print("\n[SUCCESS] Path to downloaded files:", path)
    except Exception as e:
        print("\n[ERROR] Failed to download:", e)
        print("Note: To download competition datasets, you must have kaggle.json configured")
        print("AND you must accept the competition rules on Kaggle's website first!")

if __name__ == "__main__":
    download_dataset()
