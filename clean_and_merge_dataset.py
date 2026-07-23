"""
Dataset Cleanup & Merge Script
- Merges 34 duplicate class groups into canonical names
- Removes junk classes (models, train_images, images)
- Creates a clean dataset_clean directory (original untouched)
- Copies files using shutil (no data loss)
"""
import os
import shutil
from collections import defaultdict

SRC = r'C:\Users\hp\.gemini\antigravity-ide\scratch\mitti\dataset_master'
DST = r'C:\Users\hp\.gemini\antigravity-ide\scratch\mitti\dataset_clean'

# Junk classes to completely remove
JUNK_CLASSES = {'models', 'train_images', 'images'}

# Manual merge map: all variations -> canonical name
# Format: 'original_folder_name': 'canonical_name'
MERGE_MAP = {
    # Cassava
    'Cassava___Healthy': 'Cassava_Healthy',
    'Cassava healthy': 'Cassava_Healthy',
    # Sugarcane Healthy
    'Sugarcane___Healthy': 'Sugarcane_Healthy',
    'Sugarcane_Healthy': 'Sugarcane_Healthy',
    'Sugarcane Healthy': 'Sugarcane_Healthy',
    # Wheat Healthy
    'healthy_wheat': 'Wheat_Healthy',
    'Healthy Wheat': 'Wheat_Healthy',
    # Bacterial Blight in cotton
    'Bacterial Blight in cotton': 'Bacterial_Blight_Cotton',
    'bacterial_blight in Cotton': 'Bacterial_Blight_Cotton',
    # Potato healthy
    'Potato healthy': 'Potato_Healthy',
    'Potato___healthy': 'Potato_Healthy',
    # Peach healthy
    'Peach healthy': 'Peach_Healthy',
    'Peach___healthy': 'Peach_Healthy',
    # Raspberry healthy
    'Raspberry healthy': 'Raspberry_Healthy',
    'Raspberry___healthy': 'Raspberry_Healthy',
    # Grape healthy
    'Grape healthy': 'Grape_Healthy',
    'Grape___healthy': 'Grape_Healthy',
    # Strawberry healthy
    'Strawberry healthy': 'Strawberry_Healthy',
    'Strawberry___healthy': 'Strawberry_Healthy',
    # Tomato mosaic virus
    'Tomato Tomato mosaic virus': 'Tomato_Mosaic_Virus',
    'Tomato___Tomato_mosaic_virus': 'Tomato_Mosaic_Virus',
    # Tomato Leaf Mold
    'Tomato_Leaf_Mold': 'Tomato_Leaf_Mold',
    'Tomato Leaf Mold': 'Tomato_Leaf_Mold',
    'Tomato___Leaf_Mold': 'Tomato_Leaf_Mold',
    # Tomato Early blight
    'Tomato_Early_blight': 'Tomato_Early_Blight',
    'Tomato Early blight': 'Tomato_Early_Blight',
    'Tomato___Early_blight': 'Tomato_Early_Blight',
    # Cherry healthy
    'Cherry (including_sour) healthy': 'Cherry_Healthy',
    'Cherry_(including_sour)___healthy': 'Cherry_Healthy',
    # Cherry Powdery mildew
    'Cherry (including sour) Powdery mildew': 'Cherry_Powdery_Mildew',
    'Cherry_(including_sour)___Powdery_mildew': 'Cherry_Powdery_Mildew',
    # Apple Cedar apple rust
    'Apple Cedar apple rust': 'Apple_Cedar_Apple_Rust',
    'Apple___Cedar_apple_rust': 'Apple_Cedar_Apple_Rust',
    # Strawberry Leaf scorch
    'Strawberry Leaf scorch': 'Strawberry_Leaf_Scorch',
    'Strawberry___Leaf_scorch': 'Strawberry_Leaf_Scorch',
    # Corn healthy
    'Corn (maize) healthy': 'Corn_Healthy',
    'Corn_(maize)___healthy': 'Corn_Healthy',
    'Corn___Healthy': 'Corn_Healthy',
    # Potato Early blight
    'Potato Early blight': 'Potato_Early_Blight',
    'Potato___Early_blight': 'Potato_Early_Blight',
    # Potato Late blight
    'Potato Late blight': 'Potato_Late_Blight',
    'Potato___Late_blight': 'Potato_Late_Blight',
    # Tomato healthy
    'Tomato_healthy': 'Tomato_Healthy',
    'Tomato healthy': 'Tomato_Healthy',
    'Tomato___healthy': 'Tomato_Healthy',
    # Tomato Spider mites
    'Tomato_Spider_mites_Two_spotted_spider_mite': 'Tomato_Spider_Mites',
    'Tomato Spider mites Two spotted spider mite': 'Tomato_Spider_Mites',
    'Tomato___Spider_mites Two-spotted_spider_mite': 'Tomato_Spider_Mites',
    'Tomato___Spider_Mites': 'Tomato_Spider_Mites',
    # Tomato Septoria leaf spot
    'Tomato_Septoria_leaf_spot': 'Tomato_Septoria_Leaf_Spot',
    'Tomato septoria leaf spot': 'Tomato_Septoria_Leaf_Spot',
    'Tomato___Septoria_leaf_spot': 'Tomato_Septoria_Leaf_Spot',
    # Blueberry healthy
    'Blueberry healthy': 'Blueberry_Healthy',
    'Blueberry___healthy': 'Blueberry_Healthy',
    # Tomato Late blight
    'Tomato_Late_blight': 'Tomato_Late_Blight',
    'Tomato Late blight': 'Tomato_Late_Blight',
    'Tomato___Late_blight': 'Tomato_Late_Blight',
    # Apple healthy
    'Apple healthy': 'Apple_Healthy',
    'Apple___healthy': 'Apple_Healthy',
    # Tomato Target Spot
    'Tomato Target Spot': 'Tomato_Target_Spot',
    'Tomato___Target_Spot': 'Tomato_Target_Spot',
    # Tomato Bacterial spot
    'Tomato_Bacterial_spot': 'Tomato_Bacterial_Spot',
    'Tomato Bacterial spot': 'Tomato_Bacterial_Spot',
    'Tomato___Bacterial_spot': 'Tomato_Bacterial_Spot',
    # Grape Leaf blight
    'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)': 'Grape_Leaf_Blight',
    'Grape Leaf blight Isariopsis Leaf Spot': 'Grape_Leaf_Blight',
    'Grape___Leaf_Blight': 'Grape_Leaf_Blight',
    # Grape Esca
    'Grape___Esca_(Black_Measles)': 'Grape_Esca_Black_Measles',
    'Grape Esca Black Measles': 'Grape_Esca_Black_Measles',
    # Grape Black rot
    'Grape___Black_rot': 'Grape_Black_Rot',
    'Grape Black rot': 'Grape_Black_Rot',
    # Orange
    'Orange___Haunglongbing_(Citrus_greening)': 'Orange_Citrus_Greening',
    'Orange Haunglongbing Citrus greening': 'Orange_Citrus_Greening',
    # Soybean healthy
    'Soybean___healthy': 'Soybean_Healthy',
    'Soybean healthy': 'Soybean_Healthy',
    # Apple Apple scab
    'Apple___Apple_scab': 'Apple_Apple_Scab',
    'Apple Apple scab': 'Apple_Apple_Scab',
    # Apple Black rot
    'Apple___Black_rot': 'Apple_Black_Rot',
    'Apple Black rot': 'Apple_Black_Rot',
    # Additional normalizations for classes with ___ format
    'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot': 'Corn_Cercospora_Leaf_Spot',
    'Corn___Gray_Leaf_Spot': 'Corn_Cercospora_Leaf_Spot',
    'Corn_(maize)___Common_rust_': 'Corn_Common_Rust',
    'Corn___Common_Rust': 'Corn_Common_Rust',
    'Corn_(maize)___Northern_Leaf_Blight': 'Corn_Northern_Leaf_Blight',
    'Corn___Northern_Leaf_Blight': 'Corn_Northern_Leaf_Blight',
    # Wheat duplicates
    'Wheat___Brown_Rust': 'Wheat_Brown_Rust',
    'Wheat___Healthy': 'Wheat_Healthy',
    'Wheat___Yellow_Rust': 'Wheat_Yellow_Rust',
    # Rice duplicates
    'Rice___Healthy': 'Rice_Healthy',
    'Rice___Leaf_Blast': 'Rice_Leaf_Blast',
    'Rice___Neck_Blast': 'Rice_Neck_Blast',
    # Banana
    'Banana___Black_Sigatoka': 'Banana_Black_Sigatoka',
    'Banana___Healthy': 'Banana_Healthy',
    'Banana___Panama_Disease': 'Banana_Panama_Disease',
    # Cassava
    'Cassava___Brown_Streak_Disease': 'Cassava_Brown_Streak_Disease',
    'Cassava___Mosaic_Disease': 'Cassava_Mosaic_Disease',
    # Tea
    'Tea___Algal_Leaf_Spot': 'Tea_Algal_Leaf_Spot',
    'Tea___Healthy': 'Tea_Healthy',
    # Sugarcane
    'Sugarcane___Healthy': 'Sugarcane_Healthy',
    # Pepper
    'Pepper___Healthy': 'Pepper_Healthy',
    'Pepper,_bell___Bacterial_spot': 'Pepper_Bacterial_Spot',
    'Pepper,_bell___healthy': 'Pepper_Healthy',
    # Papaya
    'Papaya___Ringspot_Virus': 'Papaya_Ringspot_Virus',
    # Squash
    'Squash___Powdery_mildew': 'Squash_Powdery_Mildew',
    # Tomato YLCV
    'Tomato___Tomato_Yellow_Leaf_Curl_Virus': 'Tomato_Yellow_Leaf_Curl_Virus',
    'Tomato Yellow Leaf Curl Virus': 'Tomato_Yellow_Leaf_Curl_Virus',
}


def get_canonical_name(folder_name):
    """Get canonical name for a folder. If no merge rule, normalize the name."""
    if folder_name in MERGE_MAP:
        return MERGE_MAP[folder_name]
    # Default normalization: replace spaces and ___ with _
    name = folder_name.replace('___', '_').replace('  ', ' ').replace(' ', '_')
    # Remove trailing underscores
    name = name.strip('_')
    return name


def main():
    if os.path.exists(DST):
        print(f"Removing existing {DST}...")
        shutil.rmtree(DST)

    os.makedirs(DST)

    src_classes = [c for c in sorted(os.listdir(SRC)) if os.path.isdir(os.path.join(SRC, c))]
    print(f"Source classes: {len(src_classes)}")

    # Build merge plan
    merge_plan = defaultdict(list)  # canonical -> [(src_folder, file_count)]
    skipped = []

    for cls in src_classes:
        if cls in JUNK_CLASSES:
            src_path = os.path.join(SRC, cls)
            file_count = len([f for f in os.listdir(src_path) if os.path.isfile(os.path.join(src_path, f))])
            skipped.append((cls, file_count))
            continue

        canonical = get_canonical_name(cls)
        src_path = os.path.join(SRC, cls)
        files = [f for f in os.listdir(src_path) if os.path.isfile(os.path.join(src_path, f))]
        merge_plan[canonical].append((cls, len(files)))

    print(f"\nSkipped junk classes:")
    for name, count in skipped:
        print(f"  {name}: {count} images (REMOVED)")

    print(f"\nCanonical classes after merge: {len(merge_plan)}")

    # Execute merge: copy files
    total_copied = 0
    class_counts = {}

    for canonical, sources in sorted(merge_plan.items()):
        dst_path = os.path.join(DST, canonical)
        os.makedirs(dst_path, exist_ok=True)

        class_total = 0
        for src_folder, _ in sources:
            src_path = os.path.join(SRC, src_folder)
            files = [f for f in os.listdir(src_path) if os.path.isfile(os.path.join(src_path, f))]

            for f in files:
                src_file = os.path.join(src_path, f)
                # Prefix with source folder hash to avoid filename collisions
                dst_file = os.path.join(dst_path, f)
                if os.path.exists(dst_file):
                    # Add prefix to avoid collision
                    base, ext = os.path.splitext(f)
                    dst_file = os.path.join(dst_path, f"{base}_{hash(src_folder) % 10000}{ext}")

                shutil.copy2(src_file, dst_file)
                class_total += 1
                total_copied += 1

        class_counts[canonical] = class_total

        if len(sources) > 1:
            src_names = [s[0] for s in sources]
            print(f"  MERGED {src_names} -> {canonical} ({class_total} images)")

    # Report
    sorted_counts = sorted(class_counts.items(), key=lambda x: x[1])
    print(f"\n{'='*60}")
    print(f"CLEANUP COMPLETE")
    print(f"{'='*60}")
    print(f"Original classes: {len(src_classes)}")
    print(f"Clean classes: {len(class_counts)}")
    print(f"Total images copied: {total_copied}")
    print(f"Min images: {sorted_counts[0][1]} ({sorted_counts[0][0]})")
    print(f"Max images: {sorted_counts[-1][1]} ({sorted_counts[-1][0]})")

    print(f"\nSmallest 20 classes (candidates for augmentation):")
    for name, count in sorted_counts[:20]:
        print(f"  {count:6d}  {name}")

    print(f"\nLargest 10 classes:")
    for name, count in sorted_counts[-10:]:
        print(f"  {count:6d}  {name}")

    # Classes still under 100 images
    small = [x for x in sorted_counts if x[1] < 100]
    print(f"\nClasses still under 100 images: {len(small)}")
    for name, count in small:
        print(f"  {count:6d}  {name}")


if __name__ == '__main__':
    main()
