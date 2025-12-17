import cv2
import face_recognition
import numpy as np
import tkinter as tk
from tkinter import filedialog
from PIL import Image
import pyttsx3
import os

# ---------- SETUP ----------
engine = pyttsx3.init()
engine.setProperty("rate", 160)

REFERENCE_DIR = "reference"
ALERT_DIR = "alerts"
os.makedirs(REFERENCE_DIR, exist_ok=True)
os.makedirs(ALERT_DIR, exist_ok=True)

reference_encoding = None
alert_triggered = False


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

    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.jpg *.png *.jpeg")]
    )
    if not file_path:
        return

    image = face_recognition.load_image_file(file_path)
    encodings = face_recognition.face_encodings(image)

    if not encodings:
        status_label.config(text="❌ No face found", fg="red")
        return

    reference_encoding = encodings[0]
    Image.open(file_path).save(os.path.join(REFERENCE_DIR, "uploaded.jpg"))

    status_label.config(text="✅ Reference image loaded", fg="lime")


# ---------- LIVE CAMERA ----------
def start_camera():
    global alert_triggered
    alert_triggered = False

    if reference_encoding is None:
        status_label.config(text="⚠ Upload reference image first", fg="orange")
        return

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)

        for (top, right, bottom, left), face_encoding in zip(locations, encodings):

            distance = face_recognition.face_distance(
                [reference_encoding], face_encoding
            )[0]

            confidence = max(0, min((1 - distance) * 100, 100))
            status, color = get_status(confidence)

            # Face box
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # Label background
            cv2.rectangle(frame, (left, top - 35), (right, top), color, cv2.FILLED)

            # Label text
            cv2.putText(
                frame,
                f"{status}  {confidence:.1f}%",
                (left + 5, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            # ---------- ALERT ----------
            if confidence > 90 and not alert_triggered:
                alert_triggered = True

                engine.say("Alert. Person detected.")
                engine.runAndWait()

                face_img = frame[top:bottom, left:right]
                cv2.imwrite(os.path.join(ALERT_DIR, "FOUND_person.jpg"), face_img)

        # Global alert banner
        if alert_triggered:
            cv2.putText(
                frame,
                "⚠ ALERT : PERSON FOUND ⚠",
                (40, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3
            )

        cv2.imshow("PERSONNEL DETECTION SECURITY SYSTEM", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# ---------- TKINTER GUI ----------
import tkinter as tk

root = tk.Tk()
root.title("PERSONNEL DETECTION SECURITY SYSTEM")
root.configure(bg="#1e1e1e")

# Fullscreen size (already working for you)
root.update_idletasks()
sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry(f"{sw}x{sh}+0+0")

# ------------------ OUTER FRAME (FULL WINDOW) ------------------
outer = tk.Frame(root, bg="#1e1e1e")
outer.pack(expand=True, fill="both")

# ------------------ CENTER FRAME ------------------
center = tk.Frame(outer, bg="#1e1e1e")
center.pack(expand=True)

# ------------------ RESPONSIVE SIZES ------------------
TITLE_FONT_SIZE = int(sh * 0.04)     # ~4% of screen height
BUTTON_FONT_SIZE = int(sh * 0.022)
BUTTON_WIDTH = int(sw * 0.035)       # ~50% screen width

# ------------------ TITLE ------------------
tk.Label(
    center,
    text="PERSONNEL DETECTION SYSTEM",
    fg="white",
    bg="#1e1e1e",
    font=("Segoe UI", TITLE_FONT_SIZE, "bold")
).pack(pady=(20, 60))

# ------------------ BUTTONS ------------------
tk.Button(
    center,
    text="Upload Image",
    command=upload_image,
    width=BUTTON_WIDTH,
    height=2,
    bg="#007acc",
    fg="white",
    font=("Segoe UI", BUTTON_FONT_SIZE, "bold"),
    bd=0
).pack(pady=20)

tk.Button(
    center,
    text="Start the search",
    command=start_camera,
    width=BUTTON_WIDTH,
    height=2,
    bg="#28a745",
    fg="white",
    font=("Segoe UI", BUTTON_FONT_SIZE, "bold"),
    bd=0
).pack(pady=20)

# ------------------ STATUS ------------------
status_label = tk.Label(
    center,
    text="System Ready",
    fg="cyan",
    bg="#1e1e1e",
    font=("Segoe UI", int(sh * 0.018))
)
status_label.pack(pady=(50, 10))

tk.Label(
    center,
    text="Press Q to stop camera",
    fg="gray",
    bg="#1e1e1e",
    font=("Segoe UI", int(sh * 0.014))
).pack()

root.mainloop()
