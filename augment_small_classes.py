"""
Augment Small Classes
- For classes with fewer than MIN_IMAGES, generates augmented copies
- Uses PIL-based transforms (rotation, flip, brightness, contrast, crop)
- Operates IN-PLACE on dataset_clean
"""
import os
import random
from PIL import Image, ImageEnhance, ImageFilter

DATASET = r'C:\Users\hp\.gemini\antigravity-ide\scratch\mitti\dataset_clean'
MIN_IMAGES = 100  # Minimum images per class


def augment_image(img):
    """Apply random augmentations to a PIL Image."""
    transforms = []
    
    # Random horizontal flip
    if random.random() > 0.5:
        transforms.append(('hflip', lambda i: i.transpose(Image.FLIP_LEFT_RIGHT)))
    
    # Random vertical flip
    if random.random() > 0.5:
        transforms.append(('vflip', lambda i: i.transpose(Image.FLIP_TOP_BOTTOM)))
    
    # Random rotation
    angle = random.uniform(-30, 30)
    transforms.append(('rotate', lambda i: i.rotate(angle, fillcolor=(0, 0, 0))))
    
    # Random brightness
    factor = random.uniform(0.7, 1.3)
    transforms.append(('brightness', lambda i: ImageEnhance.Brightness(i).enhance(factor)))
    
    # Random contrast
    factor2 = random.uniform(0.7, 1.3)
    transforms.append(('contrast', lambda i: ImageEnhance.Contrast(i).enhance(factor2)))
    
    # Random color saturation
    if random.random() > 0.5:
        factor3 = random.uniform(0.8, 1.2)
        transforms.append(('saturation', lambda i: ImageEnhance.Color(i).enhance(factor3)))
    
    # Random crop and resize
    if random.random() > 0.5:
        w, h = img.size
        crop_pct = random.uniform(0.8, 0.95)
        new_w, new_h = int(w * crop_pct), int(h * crop_pct)
        left = random.randint(0, w - new_w)
        top = random.randint(0, h - new_h)
        transforms.append(('crop', lambda i: i.crop((left, top, left + new_w, top + new_h)).resize((w, h), Image.LANCZOS)))
    
    # Random slight blur
    if random.random() > 0.7:
        transforms.append(('blur', lambda i: i.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.5, 1.5)))))
    
    # Apply a random subset of transforms
    random.shuffle(transforms)
    num_to_apply = random.randint(2, min(4, len(transforms)))
    
    for name, transform in transforms[:num_to_apply]:
        try:
            img = transform(img)
        except Exception:
            pass
    
    return img


def main():
    classes = [c for c in sorted(os.listdir(DATASET)) if os.path.isdir(os.path.join(DATASET, c))]
    
    augmented_total = 0
    classes_augmented = 0
    
    for cls in classes:
        cls_path = os.path.join(DATASET, cls)
        files = [f for f in os.listdir(cls_path) if os.path.isfile(os.path.join(cls_path, f))]
        
        if len(files) >= MIN_IMAGES:
            continue
        
        needed = MIN_IMAGES - len(files)
        print(f"  {cls}: {len(files)} images -> need {needed} more")
        classes_augmented += 1
        
        generated = 0
        attempts = 0
        max_attempts = needed * 5  # Safety limit
        
        while generated < needed and attempts < max_attempts:
            attempts += 1
            # Pick a random source image
            src_file = random.choice(files)
            src_path = os.path.join(cls_path, src_file)
            
            try:
                img = Image.open(src_path).convert('RGB')
                aug_img = augment_image(img)
                
                base, ext = os.path.splitext(src_file)
                aug_filename = f"{base}_aug_{generated}{ext}"
                aug_path = os.path.join(cls_path, aug_filename)
                
                aug_img.save(aug_path, quality=95)
                generated += 1
                augmented_total += 1
            except Exception as e:
                print(f"    Warning: Could not augment {src_file}: {e}")
                continue
        
        final_count = len([f for f in os.listdir(cls_path) if os.path.isfile(os.path.join(cls_path, f))])
        print(f"    -> Now has {final_count} images (+{generated} augmented)")
    
    print(f"\n{'='*60}")
    print(f"AUGMENTATION COMPLETE")
    print(f"{'='*60}")
    print(f"Classes augmented: {classes_augmented}")
    print(f"Total images generated: {augmented_total}")
    
    # Final verification
    print(f"\nFinal class distribution:")
    final_counts = []
    for cls in classes:
        cls_path = os.path.join(DATASET, cls)
        count = len([f for f in os.listdir(cls_path) if os.path.isfile(os.path.join(cls_path, f))])
        final_counts.append((cls, count))
    
    final_counts.sort(key=lambda x: x[1])
    still_small = [x for x in final_counts if x[1] < MIN_IMAGES]
    print(f"Classes still under {MIN_IMAGES}: {len(still_small)}")
    print(f"Total classes: {len(final_counts)}")
    total = sum(c for _, c in final_counts)
    print(f"Total images: {total}")


if __name__ == '__main__':
    main()
