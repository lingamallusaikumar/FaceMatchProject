import os
import dlib
import face_recognition
import mediapipe as mp
import numpy as np
import cv2
from FaceMetrics import FaceMetrics

# Initialize Mediapipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Set up video capture
cap = cv2.VideoCapture(0)


EYE_AR_THRESH = 0.25
MOUTH_AR_THRESH = 0.98
EYE_AR_CONSEC_imageS = 3
COUNTER = 5

KNOWN_FACES_DIR =  "../registered_faces" # training data
TOLERANCE = 0.4
image_THICKNESS = 1 # rectangle thickness
FONT_THICKNESS = 2 # font thickness
MODEL = "cnn" # convolutional
print("loading known faces")
known_faces = [] # store known faces here
known_names = [] # store name of them here
print(dlib.DLIB_USE_CUDA) # ture, if cuda is enabled.
### TRAIN THE CNN MODEL ON KNOWN FACES #############################
for name in os.listdir(KNOWN_FACES_DIR):
    for filename in os.listdir(f"{KNOWN_FACES_DIR}/{name}"):
        image = face_recognition.load_image_file(f"{KNOWN_FACES_DIR}/{name}/{filename}")
        encoding = face_recognition.face_encodings(image)[0]
        known_faces.append(encoding)
        known_names.append(name)
        


with mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5) as face_mesh:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert frame to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    locations = face_recognition.face_locations(image,model=MODEL) # find face
    encodings = face_recognition.face_encodings(image, locations) # extrac face features
    for face_encoding, face_location in zip(encodings, locations):
        if len(face_encoding) == 0:
            continue  # Skip if encoding not found

        results = face_recognition.compare_faces(known_faces, face_encoding)
        face_dist = face_recognition.face_distance(known_faces, face_encoding)
        print(f"Face distances: {face_dist}")

        matchIndex = np.argmin(face_dist)
        match = "Unknown"
        if results[matchIndex] and face_dist[matchIndex]<=TOLERANCE: # if there is a known face
            match = known_names[matchIndex] # who that person is
            print(f"Match found: {match}")
            ### DRAW RECTANGLE AND #####################################
            top_left = (face_location[3], face_location[0])
            bottom_right = (face_location[1], face_location[2])
            color = [0, 255, 0] # green 
            cv2.rectangle(image, top_left, bottom_right, color, image_THICKNESS)
            top_left = (face_location[3], face_location[2])
            bottom_right = (face_location[1], face_location[2]+22)
            cv2.rectangle(image, top_left, bottom_right, color, cv2.FILLED)
            cv2.putText(image, match, (face_location[3]+10, face_location[2]+15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), FONT_THICKNESS)
        
        

        # Show the frame
        cv2.imshow("Face Metrics", image)

        # Exit on pressing 'q'
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
