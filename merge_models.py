import os
import numpy as np
from tensorflow.keras.models import load_model

def average_weights(models_paths, output_path):
    print("Loading all models to perform Federated Weight Averaging...")
    
    # Load all models
    models = []
    for path in models_paths:
        if os.path.exists(path):
            print(f"Loading {path}...")
            models.append(load_model(path))
        else:
            print(f"Warning: {path} not found. Skipping.")
            
    if not models:
        print("Error: No models loaded. Cannot average.")
        return

    print("Extracting weights from the models...")
    # Get weights from the first model as a template
    new_weights = list(models[0].get_weights())
    
    # Loop over the remaining models and add their weights
    for model in models[1:]:
        model_weights = model.get_weights()
        for i in range(len(new_weights)):
            new_weights[i] += model_weights[i]
            
    # Average the weights
    print(f"Averaging weights across {len(models)} models...")
    for i in range(len(new_weights)):
        new_weights[i] /= len(models)
        
    print("Injecting averaged weights into a combined master model...")
    # Use the first model architecture to save the combined weights
    combined_model = models[0]
    combined_model.set_weights(new_weights)
    
    print(f"Saving combined model to {output_path}...")
    combined_model.save(output_path)
    print("Merge Complete! The Master Federated Model is ready.")

if __name__ == '__main__':
    paths = [f"model_batch_{i+1}.h5" for i in range(5)]
    average_weights(paths, "combined_model.h5")
