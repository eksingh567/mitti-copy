import os
import argparse
try:
    from bing_image_downloader import downloader
except ImportError:
    print("Please install bing-image-downloader: pip install bing-image-downloader")
    exit(1)

def scrape_disease_images(crop, disease, limit=100, output_dir='dataset'):
    """
    Scrapes images from Bing for a specific crop and disease to augment your dataset.
    """
    query = f"{crop} leaf {disease}"
    print(f"Scraping {limit} images for: '{query}'...")
    
    # We save directly into the format expected by our train_model.py script
    # e.g., dataset/Tomato___Late_blight/
    class_folder = f"{crop}___{disease.replace(' ', '_')}"
    
    downloader.download(
        query,
        limit=limit,
        output_dir=output_dir,
        adult_filter_off=True,
        force_replace=False,
        timeout=60,
        verbose=True
    )
    
    # bing-image-downloader creates a folder named after the query. 
    # Let's rename it to the PlantVillage standard format so train_model.py can use it perfectly.
    downloaded_folder = os.path.join(output_dir, query)
    target_folder = os.path.join(output_dir, class_folder)
    
    if os.path.exists(downloaded_folder):
        if not os.path.exists(target_folder):
            os.makedirs(target_folder, exist_ok=True)
            
        # Move files
        for file in os.listdir(downloaded_folder):
            os.rename(os.path.join(downloaded_folder, file), os.path.join(target_folder, file))
        os.rmdir(downloaded_folder)
        
        print(f"\n[SUCCESS] Images saved to {target_folder}/")
    else:
        print(f"\n[WARNING] Could not find the downloaded folder. Check if the download succeeded.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scrape crop disease photos from the web")
    parser.add_argument('--crop', type=str, required=True, help='Name of the crop (e.g., Tomato, Wheat)')
    parser.add_argument('--disease', type=str, required=True, help='Name of the disease (e.g., Late blight, Leaf rust)')
    parser.add_argument('--limit', type=int, default=100, help='Number of images to download')
    parser.add_argument('--output', type=str, default='dataset', help='Base dataset directory')
    
    args = parser.parse_args()
    scrape_disease_images(args.crop, args.disease, args.limit, args.output)
