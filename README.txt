***LiveCam Face Recognition with Multi person matching and Threshold alert***
1.We want a upload button , where we can upload a photo through gui and save as record .
2.we should compare the live cam feed with those uploaded photo
3.The uploaded photo is then compared with the faces that are detected in the cam.
4.Show the similarity match percentage , between the uploaded image and multi faces in the cam.
5.If the match percentage is below 20 , then the words "Not the person " should appear under the box.
  If the match percentage is between 50-70 , then "Possibility chances".
  If the match percentage is 80-90, then "certainly could be the person".
  If the match is above 90 , then "FOUND THE PERSON".
6.Give an alert when the match above 90 is found.
7.Show the captured face of 90% match with "ALERT!!" as the output.

UPDATE: 17-12-25
Updating requirements that are yet to be added to the project

1. ALERT BEEP SOUND AFTER THE PICTURE SIMILARITY IS ABOVE 85 .
2. MULTIPLE FACE DETECTION IS NOT WORKING , ONLY ONE PERSON FACE IS BEING DETECTED BUT NOT MULTIPLE FACES.
3. AFTER THE FACE IS FOUND , ALERT SOUND BEEP SHOULD RING AND THE CAPTURED FACE SHOULD BE SENT TO WHATSAPP OR MAIL AS A NOTIFICATION.
4. THE PERSON'S CAPTURED FACE FROM LIVE CAM WILL GO TO CERTAIN NUMBER OR MAIL .
5. THE IP ADDRESS OF THE DEVICE THAT SENT THE CAPTURED PHOTO SHOULD BE APPEARING AS WELL , IT SHOULD BE SENT IN MAIL OR WHATSAPP








`
import cv2
import face_recognition
import numpy as np
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import pyttsx3
import os

# ---------- Setup ----------
engine = pyttsx3.init()
REFERENCE_DIR = "reference"
ALERT_DIR = "alerts"
os.makedirs(REFERENCE_DIR, exist_ok=True)
os.makedirs(ALERT_DIR, exist_ok=True)

reference_encoding = None
alert_triggered = False


# ---------- Upload Image ----------
def upload_image():
    global reference_encoding

    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.jpg *.png *.jpeg")]
    )
    if not file_path:
        return

    image = face_recognition.load_image_file(file_path)
    encodings = face_recognition.face_encodings(image)

    if not encodings:
        status_label.config(text="No face found in uploaded image", fg="red")
        return

    reference_encoding = encodings[0]
    Image.open(file_path).save(os.path.join(REFERENCE_DIR, "uploaded.jpg"))
    status_label.config(text="Reference image uploaded successfully", fg="green")


# ---------- Similarity Logic ----------
def get_status(confidence):
    if confidence < 20:
        return "Not the person"
    elif 50 <= confidence <= 70:
        return "Possibility chances"
    elif 80 <= confidence <= 90:
        return "Certainly could be the person"
    elif confidence > 90:
        return "FOUND THE PERSON"
    else:
        return "Low match"


# ---------- Live Camera ----------
def start_camera():
    global alert_triggered

    if reference_encoding is None:
        status_label.config(text="Upload reference image first!", fg="red")
        return

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb = frame[:, :, ::-1]

        # Detect faces
        locations = face_recognition.face_locations(rgb)

        # IMPORTANT FIX: do NOT pass locations here
        encodings = face_recognition.face_encodings(frame,locations)

        for (top, right, bottom, left), face_encoding in zip(locations, encodings):

            distance = face_recognition.face_distance(
                [reference_encoding], face_encoding
            )[0]

            confidence = (1 - distance) * 100
            confidence = max(0, min(confidence, 100))

            # Status logic
            if confidence < 20:
                status = "Not the person"
            elif 50 <= confidence <= 70:
                status = "Possibility chances"
            elif 80 <= confidence <= 90:
                status = "Certainly could be the person"
            elif confidence > 90:
                status = "FOUND THE PERSON"
            else:
                status = "Low match"

            color = (0, 0, 255)
            if confidence > 90:
                color = (0, 255, 0)

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            label = f"{confidence:.2f}% - {status}"
            cv2.rectangle(frame, (left, bottom - 30),
                          (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, label, (left + 5, bottom - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (255, 255, 255), 2)

            # ALERT
            if confidence > 90 and not alert_triggered:
                alert_triggered = True
                engine.say("Alert! Found the person")
                engine.runAndWait()

                face_img = frame[top:bottom, left:right]
                cv2.imwrite("alerts/FOUND_person.jpg", face_img)

        cv2.imshow("Live Face Recognition", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# ---------- GUI ----------
root = tk.Tk()
root.title("LiveCam Face Recognition Alert")
root.geometry("400x300")

tk.Button(root, text="Upload Reference Image", command=upload_image,
          width=30, height=2).pack(pady=15)

tk.Button(root, text="Start Live Camera", command=start_camera,
          width=30, height=2).pack(pady=15)

status_label = tk.Label(root, text="Waiting for action...", fg="blue")
status_label.pack(pady=10)

tk.Label(root, text="Press Q to exit camera").pack()

root.mainloop()


`
