import tensorflow as tf

print("Checking TensorFlow GPU Status...")
physical_devices = tf.config.list_physical_devices('GPU')
if len(physical_devices) > 0:
    print(f"SUCCESS: TensorFlow detected {len(physical_devices)} GPU(s):")
    for gpu in physical_devices:
        print(f" - {gpu.name}")
    print("TensorFlow is automatically routing all Neural Network calculations to the GPU!")
else:
    print("WARNING: TensorFlow did not detect a GPU. It is falling back to the CPU.")
    print("If you have an NVIDIA GPU, you may need to install the CUDA Toolkit and cuDNN.")
