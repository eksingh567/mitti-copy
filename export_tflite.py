"""
Export TFLite - Convert trained Keras weights checkpoint to optimized TensorFlow Lite format
with Float16 Quantization by reconstructing the architecture.
"""
import tensorflow as tf
import os
import argparse
import json
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense, BatchNormalization, Dropout
from tensorflow.keras.models import Model

def export_to_tflite(weights_path, tflite_output_path):
    if not os.path.exists(weights_path):
        print(f"Error: Weights checkpoint '{weights_path}' does not exist.")
        return

    print("=" * 60)
    print(f"RECONSTRUCTING MODEL AND LOADING WEIGHTS FROM {weights_path}")
    print("=" * 60)

    # 1. Determine number of classes from class_indices
    num_classes = 205
    if os.path.exists("class_indices_v2.json"):
        with open("class_indices_v2.json", "r") as f:
            class_indices = json.load(f)
            num_classes = len(class_indices)
            print(f"Detected {num_classes} classes from class_indices_v2.json")
    else:
        print(f"Warning: class_indices_v2.json not found. Defaulting to {num_classes} classes.")

    # 2. Build model architecture
    print("Building Keras model architecture...")
    base_model = EfficientNetB0(weights=None, include_top=False, input_shape=(224, 224, 3))
    
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

    # 3. Load weights
    print(f"Loading weights from checkpoint: {weights_path}...")
    model.load_weights(weights_path)
    print("Weights loaded successfully!")

    # 4. Configure converter
    print("Configuring TFLite converter...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # Apply float16 quantization (safe for accuracy, halves size)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]

    # 5. Convert model
    print("Converting model (this may take a minute)...")
    tflite_model = converter.convert()

    # 6. Save output
    with open(tflite_output_path, 'wb') as f:
        f.write(tflite_model)
        
    weights_size = os.path.getsize(weights_path) / (1024 * 1024)
    tflite_size = os.path.getsize(tflite_output_path) / (1024 * 1024)
    
    print("\n" + "=" * 60)
    print("CONVERSION SUCCESSFUL!")
    print(f"Saved TFLite model to: {tflite_output_path}")
    print(f"Weights Checkpoint Size: {weights_size:.2f} MB")
    print(f"Quantized TFLite Size: {tflite_size:.2f} MB (~{((weights_size - tflite_size) / weights_size) * 100:.1f}% reduction)")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Keras weights to TFLite")
    parser.add_argument("--model", type=str, default="crop_disease_model_v2_best_weights.h5", help="Path to weights checkpoint")
    parser.add_argument("--output", type=str, default="crop_disease_model.tflite", help="Path to output TFLite model")
    args = parser.parse_args()
    
    export_to_tflite(args.model, args.output)
