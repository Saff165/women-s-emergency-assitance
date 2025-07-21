import speech_recognition as sr
import smtplib
import geocoder
import requests
from requests.auth import HTTPBasicAuth
from twilio.rest import Client
import time
import cv2
from email.message import EmailMessage
from deepface import DeepFace

# ========== CONFIGURATION ==========

# Email setup
sender_email = "safrinfathima549@gmail.com"
sender_password = "omnz nxij hhmm ymrf"
receiver_email = "saffi6249@gmail.com"

# Twilio setup
twilio_sid = "AC6af4fb8344eb0f8238cb2f82ab72cdad"
twilio_token = "6d12933ade7d4d2b3d1fe874832cd5fd"
twilio_number = "+15086905546"
sms_receiver = "+919500981803"

# Trigger words and stress emotions
TRIGGER_WORDS = ["help", "sos", "emergency"]
STRESS_EMOTIONS = ["fear", "angry", "sad"]

# ========== FUNCTIONS ==========

def get_location():
    g = geocoder.ip('me')
    if g.ok:
        return g.latlng, g.city, g.country
    return None

def capture_image(filename="sos_image.jpg"):
    try:
        cam = cv2.VideoCapture(0)
        ret, frame = cam.read()
        if ret:
            cv2.imwrite(filename, frame)
            print(f"Image captured: {filename}")
        else:
            print("Failed to capture image.")
        cam.release()
    except Exception as e:
        print("Camera error:", e)

def send_email(location_info, image_path="sos_image.jpg"):
    latlng, city, country = location_info
    maps_url = f"https://www.google.com/maps?q={latlng[0]},{latlng[1]}"
    subject = "SOS Emergency Alert!"
    body = f"""Emergency Triggered!

Location:
Latitude: {latlng[0]}
Longitude: {latlng[1]}
City: {city}, Country: {country}

Map: {maps_url}
"""

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg.set_content(body)

    # Attach image
    try:
        with open(image_path, 'rb') as img:
            msg.add_attachment(img.read(), maintype='image', subtype='jpeg', filename=image_path)
        print("Image attached to email.")
    except Exception as e:
        print("Failed to attach image:", e)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print("Email send failed:", e)

def send_sms(location_info):
    latlng, city, country = location_info
    maps_url = f"https://www.google.com/maps?q={latlng[0]},{latlng[1]}"
    sms_body = f"SOS! Emergency detected.\nLocation: {city}, {country}\nMap: {maps_url}"

    url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
    payload = {
        'From': twilio_number,
        'To': sms_receiver,
        'Body': sms_body
    }

    try:
        response = requests.post(url, data=payload, auth=HTTPBasicAuth(twilio_sid, twilio_token))
        if response.status_code == 201:
            print("SMS sent! SID:", response.json()['sid'])
        else:
            print("SMS failed. Status:", response.status_code)
            print("Response:", response.text)
    except Exception as e:
        print("SMS send failed:", e)

def trigger_sos(emotion_reason):
    print(f"SOS Triggered due to stress emotion: {emotion_reason}")
    capture_image()
    location_info = get_location()

    if location_info:
        send_email(location_info)
        send_sms(location_info)
    else:
        print("Could not fetch location.")

def detect_emotion_once():
    print("Analyzing facial emotion after voice trigger...")

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("Webcam not accessible.")
        return

    ret, frame = cam.read()
    cam.release()

    if ret:
        frame = cv2.resize(frame, (640, 480))  # Resize for faster processing
        try:
            result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=True)
            emotion = result[0]['dominant_emotion']
            print(f"Detected Emotion: {emotion}")

            if emotion.lower() in STRESS_EMOTIONS:
                trigger_sos(emotion)
            else:
                print("Emotion is not stressful. No SOS sent.")
        except Exception as e:
            print(f"Error analyzing emotion: {e}")
    else:
        print("Failed to capture image for emotion analysis.")

# ========== VOICE LISTENER ==========

def listen_for_sos():
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = 300
    mic = sr.Microphone()
    

    print("Voice Activated SOS system started.")
    print("Say 'help', 'SOS', or 'emergency' to trigger alert.")

    try:
        while True:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                print("Listening...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)

            try:
                text = recognizer.recognize_google(audio)
                print(f"You said: {text}")

                if any(trigger.lower() in text.lower() for trigger in TRIGGER_WORDS):
                    print("Trigger word detected! Checking facial emotion...")
                    detect_emotion_once()
                    break

            except sr.UnknownValueError:
                print("Sorry, I couldn't understand.")
            except sr.RequestError as e:
                print(f"Speech recognition error: {e}")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nVoice listener stopped.")

# ========== RUN ==========

if __name__ == "__main__":
    listen_for_sos()
