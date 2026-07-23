import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
import json
import os
import argparse

def train_model(dataset_path, epochs=10, batch_size=32, model_output='crop_disease_model_unfrozen.h5', initial_weights=None):
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset path '{dataset_path}' does not exist.")
        return

    print("Loading dataset and setting up data generators...")
    print("Loading dataset using modern tf.data API...")
    
    train_dataset = tf.keras.utils.image_dataset_from_directory(
        dataset_path,
        validation_split=0.2,
        subset="training",
        seed=123,
        image_size=(224, 224),
        batch_size=batch_size,
        label_mode='categorical'
    )

    validation_dataset = tf.keras.utils.image_dataset_from_directory(
        dataset_path,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=(224, 224),
        batch_size=batch_size,
        label_mode='categorical'
    )

    class_names = train_dataset.class_names
    num_classes = len(class_names)
    print(f"Found {num_classes} classes.")

    # Apply high-speed augmentation and normalization mapping
    def augment(image, label):
        image = tf.image.random_flip_left_right(image)
        image = image / 255.0
        return image, label

    def normalize(image, label):
        return image / 255.0, label

    train_generator = train_dataset.unbatch().apply(tf.data.experimental.ignore_errors()).batch(batch_size).map(augment, num_parallel_calls=tf.data.AUTOTUNE).prefetch(tf.data.AUTOTUNE)
    validation_generator = validation_dataset.unbatch().apply(tf.data.experimental.ignore_errors()).batch(batch_size).map(normalize, num_parallel_calls=tf.data.AUTOTUNE).prefetch(tf.data.AUTOTUNE)

    # Save class indices for inference
    class_indices = {name: i for i, name in enumerate(class_names)}
    with open('class_indices.json', 'w') as f:
        json.dump(class_indices, f)
    print("Saved class indices to class_indices.json")

    print("Building MobileNetV2 model for Fine-Tuning (100% UNFROZEN)...")
    # Load MobileNetV2 without the top classification layer
    base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
    
    # UNFREEZE THE ENTIRE BASE MODEL!
    base_model.trainable = True

    # Add custom layers on top
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.2)(x)
    predictions = Dense(num_classes, activation='softmax')(x)

    model = Model(inputs=base_model.input, outputs=predictions)

    if initial_weights and os.path.exists(initial_weights):
        print(f"Loading initial weights from {initial_weights}...")
        model.load_weights(initial_weights, by_name=True, skip_mismatch=True)

    # Use a highly-reduced learning rate since we are unfreezing the entire model 
    # to avoid catastrophic forgetting of the foundational features
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=5e-5), loss='categorical_crossentropy', metrics=['accuracy'])

    print("Starting ultimate training run...")
    
    # Save the model every 1000 steps (about every 5 minutes)
    checkpoint = tf.keras.callbacks.ModelCheckpoint(
        filepath=model_output.replace('.h5', '_checkpoint.h5'),
        save_weights_only=False,
        save_freq=1000
    )

    # Add ReduceLROnPlateau to dynamically drop the learning rate when it stalls
    reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss', 
        factor=0.2, 
        patience=2, 
        min_lr=1e-7,
        verbose=1
    )

    # Train the top layer
    history = model.fit(
        train_generator,
        validation_data=validation_generator,
        epochs=epochs,
        callbacks=[checkpoint, reduce_lr]
    )

    print(f"Saving final model to {model_output}...")
    model.save(model_output)
    print(f"Model saved to {model_output}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Train Crop Disease AI Model (100% Unfrozen)")
    parser.add_argument('--dataset', type=str, default='dataset', help='Path to the dataset directory (e.g., PlantVillage)')
    parser.add_argument('--epochs', type=int, default=10, help='Number of epochs to train')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size')
    parser.add_argument('--model_output', type=str, default='crop_disease_model_ultimate.h5', help='Filename to save the trained model')
    parser.add_argument('--initial_weights', type=str, default=None, help='Load initial weights from this .h5 file')
    args = parser.parse_args()
    
    train_model(args.dataset, args.epochs, args.batch_size, args.model_output, args.initial_weights)
