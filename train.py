import face_recognition
import cv2
import numpy as np
import os
import pyttsx3

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Function to capture and save images
def capture_and_save_images():
    # Create assets directory if it doesn't exist
    if not os.path.exists('assets'):
        os.makedirs('assets')

    # Get a reference to webcam #0 (the default one)
    video_capture = cv2.VideoCapture(0)

    print("Enter the name for the images (no spaces):")
    name = input().strip().replace(' ', '_')

    # Create a directory for the person if it doesn't exist
    person_dir = os.path.join('assets', name)
    if not os.path.exists(person_dir):
        os.makedirs(person_dir)

    print("Press 's' to save the image, 'q' to quit.")
    while True:
        # Grab a single frame of video
        ret, frame = video_capture.read()

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_frame = frame[:, :, ::-1]

        # Find all the faces in the current frame of video
        face_locations = face_recognition.face_locations(rgb_frame)

        # Display the resulting image with face detection
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Display the resulting image
        cv2.imshow('Video', frame)

        # Wait for 's' to save the image or 'q' to quit
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            if face_locations:  # Check if any face was detected
                # Save the image
                image_path = os.path.join(person_dir, f"{name}_{len(os.listdir(person_dir))}.jpg")
                cv2.imwrite(image_path, frame)
                print(f"Image saved as {image_path}")
            else:
                print("No face detected. Please make sure your face is in the frame and try again.")
        elif key == ord('q'):
            break

    # Release handle to the webcam
    video_capture.release()
    cv2.destroyAllWindows()

# Function to run face detection and recognition
def run_face_detection_and_recognition():
    # Get a reference to webcam #0 (the default one)
    video_capture = cv2.VideoCapture(0)

    # Load known face encodings and names
    known_face_encodings = []
    known_face_names = []

    # Load images from the assets directory
    for person_name in os.listdir('assets'):
        person_dir = os.path.join('assets', person_name)
        for image_name in os.listdir(person_dir):
            image_path = os.path.join(person_dir, image_name)
            image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image)
            if face_encodings:  # Check if any face was detected
                face_encoding = face_encodings[0]
                known_face_encodings.append(face_encoding)
                known_face_names.append(person_name)
            else:
                print(f"No face detected in image {image_path}")

    # Initialize some variables
    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True

    while True:
        # Grab a single frame of video
        ret, frame = video_capture.read()

        # Only process every other frame of video to save time
        if process_this_frame:
            # Resize frame of video to 1/4 size for faster face recognition processing
            # small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

            # # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            # rgb_small_frame = small_frame[:, :, ::-1]

            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(frame)
            if face_locations:  # Check if any face was detected
                face_encodings = face_recognition.face_encodings(frame, face_locations)
            else:
                face_encodings = []

            face_names = []
            name = ""
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                

                # Or instead, use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                name = "Unknown"
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

                face_names.append(name)

        process_this_frame = not process_this_frame

        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            
            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)


        # Display the resulting image
        cv2.imshow('Video', frame)
        # If a face is detected, play a greeting message
        if len(name)>0 and name != "Unknown":
            engine.say(f"Hello {name}, nice to see you!")
            engine.runAndWait()

        # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release handle to the webcam
    video_capture.release()
    cv2.destroyAllWindows()

# Main function to handle user input
def main():
    while True:
        print("Enter 'R' to run face detection and recognition, 'T' to capture images, or 'Q' to quit:")
        choice = input().strip().upper()
        if choice == 'R':
            run_face_detection_and_recognition()
        elif choice == 'T':
            capture_and_save_images()
        elif choice == 'Q':
            break
        else:
            print("Invalid choice. Please enter 'R', 'T', or 'Q'.")

main()