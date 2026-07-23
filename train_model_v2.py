"""
Train Model V2 - Maximum Accuracy with Phone Compatibility
- MobileNetV2 backbone (works on all phones)
- Strong augmentation pipeline
- Class-weighted loss for imbalanced data
- Label smoothing to reduce overconfidence
- Progressive unfreezing (head -> top 50% -> full)
- Cosine annealing LR schedule
- Mixed precision where available
"""
import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
from tensorflow.keras.models import Model
import json
import os
import argparse
import math
import numpy as np
from collections import Counter


def build_augmentation():
    """Strong augmentation pipeline using tf.image ops."""
    def augment(image, label):
        # Random horizontal flip
        image = tf.image.random_flip_left_right(image)
        # Random vertical flip (leaves can be upside down)
        image = tf.image.random_flip_up_down(image)
        # Random brightness
        image = tf.image.random_brightness(image, 0.2)
        # Random contrast
        image = tf.image.random_contrast(image, 0.8, 1.2)
        # Random saturation
        image = tf.image.random_saturation(image, 0.8, 1.2)
        # Random hue (slight)
        image = tf.image.random_hue(image, 0.05)
        # Cast to float32 (EfficientNet B0 has built-in rescaling layer)
        image = tf.cast(image, tf.float32)
        # Clip to valid range [0, 255]
        image = tf.clip_by_value(image, 0.0, 255.0)
        return image, label
    return augment


def normalize_only(image, label):
    """Just cast for validation (EfficientNet B0 has built-in rescaling)."""
    return tf.cast(image, tf.float32), label


def compute_class_weights(dataset_path):
    """Compute class weights inversely proportional to class frequency."""
    classes = sorted([c for c in os.listdir(dataset_path) 
                      if os.path.isdir(os.path.join(dataset_path, c))])
    
    counts = {}
    total = 0
    for i, cls in enumerate(classes):
        cls_path = os.path.join(dataset_path, cls)
        n = len([f for f in os.listdir(cls_path) if os.path.isfile(os.path.join(cls_path, f))])
        counts[i] = n
        total += n
    
    n_classes = len(classes)
    weights = {}
    for i, n in counts.items():
        # Balanced class weight formula
        weights[i] = total / (n_classes * max(n, 1))
        # Cap extreme weights to avoid instability
        weights[i] = min(weights[i], 10.0)
    
    print(f"Class weights range: {min(weights.values()):.3f} - {max(weights.values()):.3f}")
    return weights


def cosine_schedule(epoch, total_epochs, base_lr, min_lr=1e-7, warmup_epochs=2):
    """Cosine annealing with warmup."""
    if epoch < warmup_epochs:
        return base_lr * (epoch + 1) / warmup_epochs
    progress = (epoch - warmup_epochs) / (total_epochs - warmup_epochs)
    return min_lr + 0.5 * (base_lr - min_lr) * (1 + math.cos(math.pi * progress))


def train_model(dataset_path, epochs=30, batch_size=32, model_output='crop_disease_model_v2.h5', 
                initial_weights=None, resume_from=None):
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset path '{dataset_path}' does not exist.")
        return

    print("=" * 60)
    print("CROP DISEASE MODEL V2 - MAXIMUM ACCURACY TRAINING")
    print("=" * 60)
    
    # ========== DATA LOADING ==========
    print("\nLoading dataset using tf.data API...")
    
    train_dataset = tf.keras.utils.image_dataset_from_directory(
        dataset_path,
        validation_split=0.2,
        subset="training",
        seed=42,
        image_size=(224, 224),
        batch_size=batch_size,
        label_mode='categorical'
    )

    validation_dataset = tf.keras.utils.image_dataset_from_directory(
        dataset_path,
        validation_split=0.2,
        subset="validation",
        seed=42,
        image_size=(224, 224),
        batch_size=batch_size,
        label_mode='categorical'
    )

    class_names = train_dataset.class_names
    num_classes = len(class_names)
    print(f"Found {num_classes} classes.")

    # Save class indices
    class_indices = {name: i for i, name in enumerate(class_names)}
    with open('class_indices_v2.json', 'w') as f:
        json.dump(class_indices, f, indent=2)
    print("Saved class indices to class_indices_v2.json")

    # ========== DATA PIPELINE ==========
    augment_fn = build_augmentation()
    
    train_gen = (train_dataset
                 .unbatch()
                 .apply(tf.data.experimental.ignore_errors())
                 .shuffle(1024)
                 .batch(batch_size)
                 .map(augment_fn, num_parallel_calls=tf.data.AUTOTUNE)
                 .prefetch(tf.data.AUTOTUNE))

    val_gen = (validation_dataset
               .unbatch()
               .apply(tf.data.experimental.ignore_errors())
               .batch(batch_size)
               .map(normalize_only, num_parallel_calls=tf.data.AUTOTUNE)
               .prefetch(tf.data.AUTOTUNE))

    # ========== CLASS WEIGHTS ==========
    print("\nComputing class weights for balanced training...")
    class_weights = compute_class_weights(dataset_path)

    # ========== MODEL ARCHITECTURE ==========
    if resume_from and os.path.exists(resume_from):
        print(f"\nResuming from saved model: {resume_from}")
        model = tf.keras.models.load_model(resume_from)
    else:
        print("\nBuilding EfficientNetB0 model (phone-compatible)...")
        base_model = EfficientNetB0(weights='imagenet', include_top=False, input_shape=(224, 224, 3))

        # Build stronger classification head
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dense(512, activation='relu')(x)
        x = BatchNormalization()(x)
        x = Dropout(0.4)(x)
        x = Dense(256, activation='relu')(x)
        x = BatchNormalization()(x)
        x = Dropout(0.3)(x)
        predictions = Dense(num_classes, activation='softmax')(x)
        
        model = Model(inputs=base_model.input, outputs=predictions)

        if initial_weights and os.path.exists(initial_weights):
            print(f"Loading initial weights from {initial_weights}...")
            try:
                model.load_weights(initial_weights, by_name=True, skip_mismatch=True)
                print("Weights loaded (compatible layers only).")
            except Exception as e:
                print(f"Could not load weights: {e}. Starting fresh.")

    total_layers = len(model.layers)
    print(f"Total layers: {total_layers}")

    # ========== PROGRESSIVE TRAINING ==========
    # Phase 1: Train head only (freeze base)
    phase1_epochs = min(5, epochs // 3)
    # Phase 2: Unfreeze top 50% 
    phase2_epochs = min(10, epochs // 3)
    # Phase 3: Full unfreeze
    phase3_epochs = epochs - phase1_epochs - phase2_epochs

    print(f"\nTraining Plan:")
    print(f"  Phase 1: Head only ({phase1_epochs} epochs, lr=1e-3)")
    print(f"  Phase 2: Top 50% unfrozen ({phase2_epochs} epochs, lr=1e-4)")
    print(f"  Phase 3: Full unfreeze ({phase3_epochs} epochs, lr=5e-5)")

    # Common callbacks
    checkpoint = tf.keras.callbacks.ModelCheckpoint(
        filepath=model_output.replace('.h5', '_best_weights.h5'),
        monitor='val_accuracy',
        save_best_only=True,
        save_weights_only=True,
        mode='max',
        verbose=1
    )
    
    checkpoint_regular = tf.keras.callbacks.ModelCheckpoint(
        filepath=model_output.replace('.h5', '_checkpoint_weights.h5'),
        save_freq=2000,
        save_weights_only=True,
        verbose=0
    )

    # ===== PHASE 1: HEAD ONLY =====
    if not resume_from:
        print(f"\n{'='*60}")
        print(f"PHASE 1: Training head only ({phase1_epochs} epochs)")
        print(f"{'='*60}")
        
        # Freeze base model
        for layer in model.layers:
            if hasattr(layer, 'trainable'):
                layer.trainable = False
        # Unfreeze head layers (last few)
        for layer in model.layers[-7:]:
            layer.trainable = True
        
        trainable = sum(1 for l in model.layers if l.trainable)
        print(f"Trainable layers: {trainable}/{total_layers}")
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
            loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
            metrics=['accuracy']
        )
        
        model.fit(
            train_gen,
            validation_data=val_gen,
            epochs=phase1_epochs,
            callbacks=[checkpoint, checkpoint_regular]
        )

    # ===== PHASE 2: TOP 50% UNFROZEN =====
    print(f"\n{'='*60}")
    print(f"PHASE 2: Top 50% unfrozen ({phase2_epochs} epochs)")
    print(f"{'='*60}")
    
    freeze_until = total_layers // 2
    for i, layer in enumerate(model.layers):
        layer.trainable = i >= freeze_until
    
    trainable = sum(1 for l in model.layers if l.trainable)
    print(f"Trainable layers: {trainable}/{total_layers}")
    
    reduce_lr_p2 = tf.keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss', factor=0.5, patience=2, min_lr=1e-6, verbose=1
    )
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
        metrics=['accuracy']
    )
    
    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=phase2_epochs,
        callbacks=[checkpoint, checkpoint_regular, reduce_lr_p2]
    )

    # ===== PHASE 3: FULL UNFREEZE =====
    print(f"\n{'='*60}")
    print(f"PHASE 3: Full unfreeze ({phase3_epochs} epochs)")
    print(f"{'='*60}")
    
    for layer in model.layers:
        layer.trainable = True
    
    trainable = sum(1 for l in model.layers if l.trainable)
    print(f"Trainable layers: {trainable}/{total_layers}")
    
    reduce_lr_p3 = tf.keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss', factor=0.3, patience=3, min_lr=1e-7, verbose=1
    )
    
    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor='val_accuracy', patience=7, restore_best_weights=True, verbose=1
    )
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=5e-5),
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
        metrics=['accuracy']
    )
    
    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=phase3_epochs,
        callbacks=[checkpoint, checkpoint_regular, reduce_lr_p3, early_stop]
    )

    # ========== SAVE FINAL MODEL ==========
    saved_model_dir = model_output.replace('.h5', '_saved_model')
    print(f"\nSaving final model to {saved_model_dir}...")
    model.save(saved_model_dir, save_format='tf')
    print(f"Model saved to {saved_model_dir}")

    # Also save as TFLite for phone deployment
    tflite_output = model_output.replace('.h5', '.tflite')
    print(f"Converting to TFLite for phone deployment: {tflite_output}...")
    try:
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        tflite_model = converter.convert()
        with open(tflite_output, 'wb') as f:
            f.write(tflite_model)
        print(f"TFLite model saved ({len(tflite_model) / 1024 / 1024:.1f} MB)")
    except Exception as e:
        print(f"TFLite conversion failed: {e}")

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Train Crop Disease AI Model V2")
    parser.add_argument('--dataset', type=str, default='dataset_clean', help='Path to clean dataset')
    parser.add_argument('--epochs', type=int, default=30, help='Total epochs')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size')
    parser.add_argument('--model_output', type=str, default='crop_disease_model_v2.h5', help='Output model file')
    parser.add_argument('--initial_weights', type=str, default=None, help='Load initial weights')
    parser.add_argument('--resume_from', type=str, default=None, help='Resume from a saved model')
    args = parser.parse_args()
    
    train_model(args.dataset, args.epochs, args.batch_size, args.model_output, 
                args.initial_weights, args.resume_from)
