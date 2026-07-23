import numpy as np
import cv2
import json
import tensorflow as tf

def diagnose():
    model_path = 'crop_disease_model.tflite'
    class_indices_path = 'class_indices_v2.json'
    
    interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    with open(class_indices_path, 'r') as f:
        class_indices = json.load(f)
    
    idx_to_class = {v: k for k, v in class_indices.items()}
    
    # Load or generate a test image
    img = np.zeros((224, 224, 3), dtype=np.uint8)
    img[:] = (35, 142, 35) # Forest green
    # Add some yellow patches
    cv2.circle(img, (112, 112), 40, (0, 215, 255), -1)
    
    # Try raw [0, 255] float
    input_data = np.expand_dims(img, axis=0).astype(np.float32)
    
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    predictions = interpreter.get_tensor(output_details[0]['index'])[0]
    
    # Try normalized [0, 1] float
    input_data_norm = (np.expand_dims(img, axis=0) / 255.0).astype(np.float32)
    interpreter.set_tensor(input_details[0]['index'], input_data_norm)
    interpreter.invoke()
    predictions_norm = interpreter.get_tensor(output_details[0]['index'])[0]
    
    print("--- RAW [0, 255] TOP 5 PREDICTIONS ---")
    top_indices = np.argsort(predictions)[-5:][::-1]
    for idx in top_indices:
        print(f"Class: {idx_to_class[idx]} (Index: {idx}), Score: {predictions[idx]*100:.2f}%")
        
    print("\n--- NORMALIZED [0, 1] TOP 5 PREDICTIONS ---")
    top_indices_norm = np.argsort(predictions_norm)[-5:][::-1]
    for idx in top_indices_norm:
        print(f"Class: {idx_to_class[idx]} (Index: {idx}), Score: {predictions_norm[idx]*100:.2f}%")

if __name__ == "__main__":
    diagnose()
