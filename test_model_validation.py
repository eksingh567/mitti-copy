import os
import json
import random
import numpy as np
import cv2
import tensorflow as tf

def test_validation():
    model_path = 'crop_disease_model.tflite'
    class_indices_path = 'class_indices_v2.json'
    dataset_path = '../mitti/dataset_clean'  # Path to dataset
    
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset path '{dataset_path}' not found.")
        return
        
    interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    with open(class_indices_path, 'r') as f:
        class_indices = json.load(f)
    
    idx_to_class = {v: k for k, v in class_indices.items()}
    
    # Get all class directories
    class_dirs = sorted([d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d))])
    
    print("Evaluating 20 random images from the dataset...")
    correct = 0
    total = 0
    
    # Select 20 random classes
    selected_classes = random.sample(class_dirs, min(len(class_dirs), 20))
    
    for class_name in selected_classes:
        class_dir = os.path.join(dataset_path, class_name)
        images = [f for f in os.listdir(class_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not images:
            continue
            
        img_name = random.choice(images)
        img_path = os.path.join(class_dir, img_name)
        
        # Load and preprocess image
        img = cv2.imread(img_path)
        if img is None:
            continue
            
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (224, 224))
        input_data = np.expand_dims(img_resized, axis=0).astype(np.float32)
        
        # Run prediction
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        predictions = interpreter.get_tensor(output_details[0]['index'])[0]
        
        max_idx = np.argmax(predictions)
        predicted_class = idx_to_class.get(max_idx, "Unknown")
        
        is_correct = (predicted_class == class_name)
        if is_correct:
            correct += 1
        total += 1
        
        print(f"Actual: {class_name} | Predicted: {predicted_class} | Correct: {is_correct} (Confidence: {predictions[max_idx]*100:.1f}%)")
        
    print(f"\nFinal Test Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")

if __name__ == "__main__":
    test_validation()
