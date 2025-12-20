import cv2
import face_recognition
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import pyttsx3
import os
import threading
import time
import winsound
import socket
import smtplib
import numpy as np
from email.message import EmailMessage

# ================= SETUP =================
engine = pyttsx3.init()
engine.setProperty("rate", 160)

REFERENCE_DIR = "reference"
ALERT_DIR = "alerts"
os.makedirs(REFERENCE_DIR, exist_ok=True)
os.makedirs(ALERT_DIR, exist_ok=True)

BEEP_FILE = r"C:\Users\saiku\OneDrive\Desktop\4.2 project\beep.wav"

# ================= CAMERA LOCATION =================
CAMERA_LOCATION_NAME = "Webcam - Main Gate"
CAMERA_ADDRESS = "Universal Engineering College & Technology, Dokiparru, Andhra Pradesh, India"
CAMERA_LATITUDE = "16.315213439174432"
CAMERA_LONGITUDE = "80.32502332883492"
CAMERA_MAP_URL = "https://maps.app.goo.gl/9iGu9NRNL4JY9gTM7"

reference_encoding = None
cap = None
running = False
camera_active = False

cam_window = None
video_label = None
last_captured_face = None

alert_lock = threading.Lock()
email_popup_active = False
alert_triggered = False

first_detected_time = None
DETECTION_DELAY = 3  # seconds

# ================= ALERT SOUND =================
def play_beep_and_alert():
    if alert_lock.locked():
        return

    def _alert():
        with alert_lock:
            try:
                winsound.PlaySound(BEEP_FILE, winsound.SND_FILENAME)
            except:
                pass
            engine.stop()
            engine.say("Alert. Person detected.")
            engine.runAndWait()

    threading.Thread(target=_alert, daemon=True).start()

# ================= STATUS =================
def get_status(confidence):
    if confidence < 50:
        return "LOW MATCH", (0, 165, 255)
    elif confidence < 60:
        return "POSSIBLE MATCH", (0, 255, 255)
    elif confidence < 75:
        return "HIGH CONFIDENCE", (0, 255, 0)
    else:
        return "PERSON FOUND", (0, 0, 255)

# ================= DISTANCE → CONFIDENCE =================
def distance_to_confidence(distance):
    if distance <= 0.45:
        return int(100 - (distance / 0.45) * 10)
    elif distance <= 0.50:
        return int(80 - (distance - 0.45) * 200)
    elif distance <= 0.55:
        return int(60 - (distance - 0.50) * 200)
    else:
        return max(0, int(30 - (distance - 0.55) * 100))

# ================= IP =================
def get_device_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except:
        return "IP Not Found"

# ================= EMAIL =================
def send_email(receiver_email, image_path):
    SENDER_EMAIL = "saikumarlingamallu2003@gmail.com"
    APP_PASSWORD = "syht odif fbmr usop"   # ⚠ move to env variable later

    try:
        msg = EmailMessage()
        msg["Subject"] = "🚨🚨 PERSON DETECTED ALERT 🚨🚨"
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver_email

        msg.set_content(
            f"🚨🚨🚨 PERSON DETECTED ALERT 🚨🚨🚨\n\n"
            f"Time: {time.ctime()}\n"
            f"Device IP: {get_device_ip()}\n\n"
            f"Camera Name: {CAMERA_LOCATION_NAME}\n"
            f"Address: {CAMERA_ADDRESS}\n"
            f"Latitude: {CAMERA_LATITUDE}\n"
            f"Longitude: {CAMERA_LONGITUDE}\n\n"
            f"Google Maps:\n{CAMERA_MAP_URL}"
        )

        with open(image_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="image",
                subtype="jpeg",
                filename=os.path.basename(image_path)
            )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)

    except Exception as e:
        print("Email error:", e)

# ================= EMAIL POPUP =================
def ask_email_and_send(image_path):
    global email_popup_active
    if email_popup_active:
        return
    email_popup_active = True

    popup = tk.Toplevel(root)
    popup.title("Send Alert Email")
    popup.geometry("400x200")
    popup.configure(bg="#1e1e1e")
    popup.grab_set()

    def close_popup():
        global email_popup_active
        email_popup_active = False
        popup.destroy()

    popup.protocol("WM_DELETE_WINDOW", close_popup)

    tk.Label(
        popup, text="Enter Email to Send Alert",
        bg="#1e1e1e", fg="white",
        font=("Segoe UI", 12, "bold")
    ).pack(pady=15)

    email_entry = tk.Entry(popup, width=35)
    email_entry.pack(pady=10)

    def send():
        email = email_entry.get().strip()
        if "@" not in email:
            messagebox.showerror("Invalid Email", "Enter valid email")
            return
        close_popup()
        threading.Thread(
            target=send_email,
            args=(email, image_path),
            daemon=True
        ).start()

    tk.Button(
        popup, text="Send Alert",
        command=send, bg="#28a745", fg="white"
    ).pack(pady=10)

# ================= FACE SAVE =================
def on_face_captured(face_img):
    global last_captured_face
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(ALERT_DIR, f"FOUND_{ts}.jpg")
    cv2.imwrite(path, face_img)
    last_captured_face = face_img.copy()
    root.after(0, ask_email_and_send, path)

# ================= UPLOAD IMAGE =================
def upload_image():
    global reference_encoding
    path = filedialog.askopenfilename(
        filetypes=[("Images", "*.jpg *.jpeg *.png")]
    )
    if not path:
        return

    img = face_recognition.load_image_file(path)
    enc = face_recognition.face_encodings(img)
    if not enc:
        status_label.config(text="❌ No face detected", fg="red")
        return

    reference_encoding = enc[0]
    status_label.config(text="✅ Reference image loaded", fg="lime")

# ================= CAMERA LOOP =================
def camera_loop():
    global cap, running, first_detected_time, alert_triggered

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    running = True

    while running and camera_active:
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)

        face_detected = False

        for (top, right, bottom, left), enc in zip(locations, encodings):

            if reference_encoding is None:
                continue

            dist = face_recognition.face_distance([reference_encoding], enc)[0]
            confidence = distance_to_confidence(dist)

            status, color = get_status(confidence)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(
                frame, f"{status} {confidence}%",
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
            )

            if confidence >= 65:
                face_detected = True
                now = time.time()
                if first_detected_time is None:
                    first_detected_time = now

                elapsed = int(now - first_detected_time)
                cv2.putText(
                    frame, f"Tracking: {elapsed}s / {DETECTION_DELAY}s",
                    (left, bottom + 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2
                )

                if elapsed >= DETECTION_DELAY and not alert_triggered:
                    alert_triggered = True
                    play_beep_and_alert()
                    on_face_captured(frame[top:bottom, left:right])

        if not face_detected:
            first_detected_time = None

        # ===== SHOW CAPTURED FACE AT TOP =====
        if last_captured_face is not None:
            try:
                thumb = cv2.resize(last_captured_face, (160, 160))
                h, w, _ = frame.shape
                x1 = (w - 160) // 2
                y1 = 10
                frame[y1:y1+160, x1:x1+160] = thumb
                cv2.rectangle(frame, (x1, y1), (x1+160, y1+160), (0, 0, 255), 3)
                cv2.putText(frame, "Captured Face",
                            (x1, y1 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (0, 0, 255), 2)
            except:
                pass

        # ===== FIT TO FULLSCREEN =====
        sw, sh = video_label.winfo_width(), video_label.winfo_height()
        if sw > 1 and sh > 1:
            h, w, _ = frame.shape
            scale = min(sw / w, sh / h)
            resized = cv2.resize(frame, (int(w*scale), int(h*scale)))
            canvas = np.zeros((sh, sw, 3), dtype=np.uint8)
            y, x = (sh - resized.shape[0])//2, (sw - resized.shape[1])//2
            canvas[y:y+resized.shape[0], x:x+resized.shape[1]] = resized
            frame = canvas

        img = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
        video_label.configure(image=img)
        video_label.image = img

    cap.release()

# ================= CAMERA CONTROLS =================
def start_camera():
    global camera_active, alert_triggered, email_popup_active
    global last_captured_face, first_detected_time, cam_window

    if camera_active:
        return

    if reference_encoding is None:
        status_label.config(text="⚠ Upload reference image first", fg="orange")
        return

    camera_active = True
    alert_triggered = False
    email_popup_active = False
    last_captured_face = None
    first_detected_time = None

    cam_window = tk.Toplevel(root)
    cam_window.title("Camera Feed")
    cam_window.attributes("-fullscreen", True)
    cam_window.bind("<Escape>", lambda e: stop_camera())
    cam_window.protocol("WM_DELETE_WINDOW", stop_camera)

    global video_label
    video_label = tk.Label(cam_window, bg="black")
    video_label.pack(fill="both", expand=True)

    threading.Thread(target=camera_loop, daemon=True).start()
    status_label.config(text="📷 Camera Started (FULL SCREEN)", fg="cyan")

def stop_camera():
    global running, camera_active, first_detected_time, cam_window
    running = False
    camera_active = False
    first_detected_time = None
    if cam_window:
        cam_window.destroy()
    status_label.config(text="⛔ Camera Stopped", fg="cyan")

# ================= GUI =================
root = tk.Tk()
root.title("PERSONNEL DETECTION SECURITY SYSTEM")
root.configure(bg="#1e1e1e")
root.state("zoomed")

center = tk.Frame(root, bg="#1e1e1e")
center.pack(expand=True)

tk.Label(center, text="PERSONNEL DETECTION SYSTEM",
         fg="white", bg="#1e1e1e",
         font=("Segoe UI", 28, "bold")).pack(pady=30)

tk.Button(center, text="Upload Image", command=upload_image,
          width=30, height=2, bg="#007acc", fg="white",
          font=("Segoe UI", 16, "bold")).pack(pady=10)

tk.Button(center, text="Start Camera", command=start_camera,
          width=30, height=2, bg="#28a745", fg="white",
          font=("Segoe UI", 16, "bold")).pack(pady=10)

tk.Button(center, text="Stop Camera", command=stop_camera,
          width=30, height=2, bg="#dc3545", fg="white",
          font=("Segoe UI", 16, "bold")).pack(pady=10)

status_label = tk.Label(center, text="System Ready",
                        fg="cyan", bg="#111111",
                        font=("Segoe UI", 14))
status_label.pack(pady=20)

root.mainloop()