from bing_image_downloader import downloader
import os
import shutil

dataset_dir = 'dataset_www_scrape'
os.makedirs(dataset_dir, exist_ok=True)

# A massive list of targets covering major crops and diseases
targets = {
    'Apple': ['Apple Scab', 'Black Rot', 'Cedar Apple Rust', 'Healthy'],
    'Blueberry': ['Healthy'],
    'Cherry': ['Powdery Mildew', 'Healthy'],
    'Corn': ['Cercospora Leaf Spot', 'Common Rust', 'Northern Leaf Blight', 'Healthy'],
    'Grape': ['Black Rot', 'Esca', 'Leaf Blight', 'Healthy'],
    'Orange': ['Citrus Greening'],
    'Peach': ['Bacterial Spot', 'Healthy'],
    'Pepper': ['Bacterial Spot', 'Healthy'],
    'Potato': ['Early Blight', 'Late Blight', 'Healthy'],
    'Raspberry': ['Healthy'],
    'Soybean': ['Healthy'],
    'Squash': ['Powdery Mildew'],
    'Strawberry': ['Leaf Scorch', 'Healthy'],
    'Tomato': ['Bacterial Spot', 'Early Blight', 'Late Blight', 'Leaf Mold', 'Septoria Leaf Spot', 'Spider Mites', 'Target Spot', 'Tomato Yellow Leaf Curl Virus', 'Tomato Mosaic Virus', 'Healthy']
}

print("INITIATING WWW SCRAPING PROTOCOL...")
print("Targeting up to 10,000+ images across all major crops and diseases directly from the World Wide Web.")

for crop, diseases in targets.items():
    for disease in diseases:
        query = f"{crop} leaf {disease}"
        # Format the folder to match the expected ML model structure
        formatted_disease = disease.replace(' ', '_')
        target_folder_name = f"{crop}___{formatted_disease}"
        
        print(f"\n--- Scraping WWW for: {query} ---")
        try:
            # Scrape up to 300 images per disease class directly from search engines
            downloader.download(
                query, 
                limit=300,  
                output_dir=dataset_dir, 
                adult_filter_off=False, 
                force_replace=False, 
                timeout=60, 
                verbose=False
            )
            
            bing_folder = os.path.join(dataset_dir, query)
            final_folder = os.path.join(dataset_dir, target_folder_name)
            
            if os.path.exists(bing_folder):
                if os.path.exists(final_folder):
                    # Merge images if folder already exists
                    for img in os.listdir(bing_folder):
                        shutil.move(os.path.join(bing_folder, img), os.path.join(final_folder, img))
                    os.rmdir(bing_folder)
                else:
                    # Rename to the CropName___DiseaseName format
                    os.rename(bing_folder, final_folder)
                    
        except Exception as e:
            print(f"Error scraping {query}: {e}")

print("\n=======================================================")
print("WWW MASS-SCRAPE COMPLETE!")
print(f"All images have been sorted perfectly into '{dataset_dir}'.")
print("=======================================================")
