import cv2
import sys

def test_camera():
    print("=== CAMERA DIAGNOSTICS ===")
    
    # Try indices 0, 1, 2 for available cameras
    camera_found = False
    for index in range(3):
        print(f"Testing camera index {index}...")
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)  # Use DirectShow backend for fast initialization on Windows
        
        if not cap.isOpened():
            # Fallback to default backend
            cap = cv2.VideoCapture(index)
            
        if cap.isOpened():
            print(f"-> Camera index {index} is OPEN!")
            
            # Read a frame
            ret, frame = cap.read()
            if ret:
                print(f"-> Successfully captured frame of shape: {frame.shape}")
                # Save test image
                cv2.imwrite("camera_test.jpg", frame)
                print("-> Saved test frame to 'camera_test.jpg'")
                camera_found = True
            else:
                print(f"-> Error: Camera opened but failed to read frame.")
                
            cap.release()
            break
        else:
            print(f"-> Camera index {index} could not be opened.")
            
    if not camera_found:
        print("\n[FAIL] No active camera was found or could be read. Please check Windows privacy settings or camera drivers.")
    else:
        print("\n[SUCCESS] Camera diagnostics passed! You can view 'camera_test.jpg' in the workspace directory.")

if __name__ == "__main__":
    test_camera()
