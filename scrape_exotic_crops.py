from bing_image_downloader import downloader
import os
import shutil

dataset_dir = 'dataset_www_scrape_exotic'
os.makedirs(dataset_dir, exist_ok=True)

# A list of exotic, tropical, and highly specific crop diseases
targets = {
    'Banana': ['Black Sigatoka', 'Panama Disease', 'Healthy'],
    'Mango': ['Anthracnose', 'Powdery Mildew', 'Healthy'],
    'Papaya': ['Ringspot Virus', 'Healthy'],
    'Guava': ['Fruit Canker', 'Healthy'],
    'Cacao': ['Black Pod Rot', 'Healthy'],
    'Cassava': ['Brown Streak Disease', 'Mosaic Disease', 'Healthy'],
    'Coffee': ['Rust', 'Healthy'],
    'Cotton': ['Bacterial Blight', 'Healthy'],
    'Tea': ['Algal Leaf Spot', 'Healthy'],
    'Sugarcane': ['Red Rot', 'Healthy']
}

print("INITIATING EXOTIC TROPICAL CROP SCRAPING PROTOCOL")
print("Targeting up to 10,000+ images of rare and tropical crop diseases from the Web.")

for crop, diseases in targets.items():
    for disease in diseases:
        query = f"{crop} leaf {disease}"
        formatted_disease = disease.replace(' ', '_')
        target_folder_name = f"{crop}___{formatted_disease}"
        
        print(f"\n--- Scraping WWW for: {query} ---")
        try:
            # Pushing the limit to 500 images per exotic disease
            downloader.download(
                query, 
                limit=500,  
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
                    for img in os.listdir(bing_folder):
                        shutil.move(os.path.join(bing_folder, img), os.path.join(final_folder, img))
                    os.rmdir(bing_folder)
                else:
                    os.rename(bing_folder, final_folder)
                    
        except Exception as e:
            print(f"Error scraping {query}: {e}")

print("\n=======================================================")
print("EXOTIC MASS-SCRAPE COMPLETE!")
print("=======================================================")
