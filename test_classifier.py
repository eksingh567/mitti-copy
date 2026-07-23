import numpy as np
import cv2
import json
from ml_service import CropDiseaseClassifier

# Generate synthetic test images
def generate_test_image(type):
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    if type == 'healthy':
        img[:] = (35, 142, 35) # Forest green
    elif type == 'yellow_rust':
        img[:] = (35, 142, 35)
        # Add yellow patches
        cv2.circle(img, (50, 50), 30, (0, 215, 255), -1)
        cv2.circle(img, (150, 100), 40, (0, 215, 255), -1)
    elif type == 'late_blight':
        img[:] = (35, 142, 35)
        # Add brown/black necrotic patches
        cv2.circle(img, (100, 100), 50, (19, 69, 139), -1) # Brown
        cv2.circle(img, (40, 150), 20, (0, 0, 0), -1) # Black
    
    # Encode to bytes
    success, encoded_image = cv2.imencode('.jpg', img)
    return encoded_image.tobytes()

classifier = CropDiseaseClassifier()
print('--- TEST RESULTS ---')

# Test 1: Healthy
res1 = classifier.predict(generate_test_image('healthy'), 'Wheat')
print(f"Test 1 (Mostly Green): {res1['disease']} (Confidence: {res1['confidence']}%)")

# Test 2: Yellow Rust
res2 = classifier.predict(generate_test_image('yellow_rust'), 'Wheat')
print(f"Test 2 (Green with Yellow Spots): {res2['disease']} (Confidence: {res2['confidence']}%)")

# Test 3: Late Blight (Brown spots)
res3 = classifier.predict(generate_test_image('late_blight'), 'Tomato')
print(f"Test 3 (Green with Brown/Black Spots): {res3['disease']} (Confidence: {res3['confidence']}%)")
