import cv2
import face_recognition
import numpy as np
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import pyttsx3
import os
import threading

# ---------- SETUP ----------
engine = pyttsx3.init()
engine.setProperty("rate", 160)

REFERENCE_DIR = "reference"
ALERT_DIR = "alerts"
os.makedirs(REFERENCE_DIR, exist_ok=True)
os.makedirs(ALERT_DIR, exist_ok=True)

reference_encoding = None
alert_triggered = False
cap = None  # Global webcam capture
running = False  # To stop the thread
cam_window = None  # Toplevel window for camera
video_label = None  # Label inside Toplevel to show video


# ---------- STATUS LOGIC ----------
def get_status(confidence):
    if confidence < 30:
        return "NOT A MATCH", (0, 0, 255)
    elif 30 <= confidence < 50:
        return "LOW MATCH", (0, 165, 255)
    elif 60 <= confidence < 75:
        return "POSSIBLE MATCH", (0, 255, 255)
    elif 80 <= confidence < 85:
        return "HIGH CONFIDENCE", (0, 255, 0)
    else:
        return "⚠ FOUND PERSON", (0, 255, 0)


# ---------- UPLOAD IMAGE ----------
def upload_image():
    global reference_encoding

    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg")])
    if not file_path:
        return

    image = face_recognition.load_image_file(file_path)
    encodings = face_recognition.face_encodings(image)

    if not encodings:
        status_label.config(text="❌ No face found", fg="red")
        return

    reference_encoding = encodings[0]
    status_label.config(text="✅ Reference image loaded", fg="lime")


# ---------- CAMERA THREAD ----------
def camera_loop_tk():
    global cap, alert_triggered, running, video_label

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        status_label.config(text="❌ Cannot access webcam", fg="red")
        return

    alert_triggered = False
    running = True

    while running:
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)

        for (top, right, bottom, left), face_encoding in zip(locations, encodings):
            distance = face_recognition.face_distance([reference_encoding], face_encoding)[0]
            confidence = max(0, min((1 - distance) * 100, 100))
            status, color = get_status(confidence)

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, top - 35), (right, top), color, cv2.FILLED)
            cv2.putText(frame, f"{status} {confidence:.1f}%", (left + 5, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            if confidence > 90 and not alert_triggered:
                alert_triggered = True
                engine.say("Alert. Person detected.")
                engine.runAndWait()
                face_img = frame[top:bottom, left:right]
                cv2.imwrite(os.path.join(ALERT_DIR, "FOUND_person.jpg"), face_img)

        if alert_triggered:
            cv2.putText(frame, "⚠ ALERT : PERSON FOUND ⚠", (40, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

        # Convert frame to ImageTk for Tkinter
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=img)

        if video_label:
            video_label.imgtk = imgtk
            video_label.configure(image=imgtk)

        # Small delay to allow Tkinter to update
        if not running:
            break
        if video_label:
            video_label.update()

    cap.release()
    running = False
    if cam_window:
        cam_window.destroy()


# ---------- START CAMERA ----------
def start_camera():
    global cam_window, video_label

    if reference_encoding is None:
        status_label.config(text="⚠ Upload reference image first", fg="orange")
        return

    # Create new Toplevel window
    cam_window = tk.Toplevel(root)
    cam_window.title("Camera Feed")
    cam_window.configure(bg="black")
    cam_window.protocol("WM_DELETE_WINDOW", stop_camera)  # Handle window close

    video_label = tk.Label(cam_window, bg="black")
    video_label.pack()

    threading.Thread(target=camera_loop_tk, daemon=True).start()
    status_label.config(text="Camera started", fg="cyan")


# ---------- STOP CAMERA ----------
def stop_camera():
    global running
    running = False
    status_label.config(text="Camera stopped", fg="cyan")
    if cam_window:
        cam_window.destroy()


# ---------- TKINTER GUI ----------
root = tk.Tk()
root.title("PERSONNEL DETECTION SECURITY SYSTEM")
root.configure(bg="#1e1e1e")

sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry(f"{sw}x{sh}+0+0")

center = tk.Frame(root, bg="#1e1e1e")
center.pack(expand=True)

TITLE_FONT_SIZE = int(sh * 0.04)
BUTTON_FONT_SIZE = int(sh * 0.022)
BUTTON_WIDTH = int(sw * 0.035)

tk.Label(center, text="PERSONNEL DETECTION SYSTEM", fg="white", bg="#1e1e1e",
         font=("Segoe UI", TITLE_FONT_SIZE, "bold")).pack(pady=(20, 30))

tk.Button(center, text="Upload Image", command=upload_image, width=BUTTON_WIDTH,
          height=2, bg="#007acc", fg="white", font=("Segoe UI", BUTTON_FONT_SIZE, "bold"),
          bd=0).pack(pady=10)

tk.Button(center, text="Start Camera", command=start_camera, width=BUTTON_WIDTH,
          height=2, bg="#28a745", fg="white", font=("Segoe UI", BUTTON_FONT_SIZE, "bold"),
          bd=0).pack(pady=10)

tk.Button(center, text="Stop Camera", command=stop_camera, width=BUTTON_WIDTH,
          height=2, bg="#dc3545", fg="white", font=("Segoe UI", BUTTON_FONT_SIZE, "bold"),
          bd=0).pack(pady=10)

status_label = tk.Label(center, text="System Ready", fg="cyan", bg="#111111",
                        font=("Segoe UI", int(sh * 0.018)))
status_label.pack(pady=(20, 10))

root.mainloop()