import time
from picamera2 import Picamera2
import subprocess
import os
from gtts import gTTS
import multiprocessing
import RPi.GPIO as GPIO
import serial
import pynmea2
import yagmail
import google.generativeai as genai
from PIL import Image

# Initialize camera
def initialize_camera():
    camera = Picamera2()
    camera_config = camera.create_still_configuration(main={"size": (640, 480)})
    camera.configure(camera_config)
    camera.start()
    return camera

# Configure Gemini API
genai.configure(api_key="YOUR_API_KEY")

# Email Configuration
EMAIL_SENDER = "BLIND_PERSON_EMAIL_ID"
EMAIL_PASSWORD = "PASSWORD"
EMAIL_RECEIVER = "GUARDIAN_EMAIL_ID"

# Button Configuration
BUTTON_PIN = 17  # GPIO Pin for the emergency button
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def capture_image(camera):
    """Capture an image and save it."""
    filename = '/home/gurup/blind_navigation/test.jpg'
    camera.capture_file(filename)
    print(f"Image saved to {filename}")
    return filename

def get_navigation_instructions(image_path):
    """Send image to Google Gemini API for navigation instructions."""
    print("Processing image for navigation instructions...")
    
    try:
        # Load the image
        image = Image.open(image_path)
        
        # Set up the model
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Prompt for navigation guidance
        prompt = """
        RESPOND WITH CONCISE NAVIGATION DIRECTIONS ONLY. NO PREAMBLE.

        You are guiding a blind person through their environment. Provide clear, actionable navigation cues using the following structure:

        1. ORIENTATION (5-10 words)  
        - Describe the general environment.  
        - Examples:  
            - "Office hallway with doorways ahead."  
            - "Crowded sidewalk with moving pedestrians."  

        2. IMMEDIATE PATH (1-2 short sentences)  
        - Provide clear guidance on the safest route forward.  
        - Examples:  
            - "Walk straight for 3 meters; clear path ahead."  
            - "Turn left to avoid an obstacle in front."  

        3. HAZARDS & ACTION (If present)  
        - Mention immediate dangers and suggest what to do.  
        - Examples:  
            - "CAUTION: Steps down in 2 meters—slow down and reach for the handrail on your left."  
            - "CAUTION: Person approaching from the left—pause and let them pass."  
            - "DANGER: Person carrying a knife walking toward you—step back and move right."  

        4. LANDMARKS (If helpful)  
        - Mention useful orientation points to aid navigation.  
        - Examples:  
            - "Doorway on your right in 4 meters."  
            - "Handrail available on your left."  

        5. NEXT ACTION SUGGESTION (If needed)  
        - Provide a brief suggestion on what to do next after avoiding a hazard or reaching a destination.  
        - Examples:  
            - "Continue straight for 5 meters to reach the exit."  
            - "After turning right, listen for crossing signal before proceeding."  

        Guidelines:  
        - Keep responses under 80 words.  
        - Use specific distances (meters/feet) for clarity.  
        - Prioritize safety information.  
        - Provide immediate and actionable suggestions.  
        """

        
        response = model.generate_content([prompt, image])
        navigation_text = response.text
        print(f"Navigation instructions: {navigation_text}")
        return navigation_text
    except Exception as e:
        print(f"Error in generating navigation instructions: {e}")
        return "Navigation system is currently unavailable."



def speak_text(text):
    """Convert text to speech and play it."""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save("output.mp3")
        subprocess.run(["ffplay", "-nodisp", "-autoexit", "-af", "atempo=1.5", "output.mp3"],
                       stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except Exception as e:
        print(f"TTS error: {e}")
        os.system(f'echo "{text}" | festival --tts')

# GPS Module Configuration - Initialize in the function where it's used
def get_gps_location():
    """Fetch GPS coordinates from the NEO-6M module."""
    try:
        # Initialize GPS only when needed to avoid resource conflicts
        gps = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)
        
        # Try for a reasonable amount of time (up to 10 seconds)
        start_time = time.time()
        while time.time() - start_time < 10:
            line = gps.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("$GPGGA") or line.startswith("$GPRMC"):
                try:
                    msg = pynmea2.parse(line)
                    lat, lon = msg.latitude, msg.longitude
                    gps.close()
                    return lat, lon
                except pynmea2.ParseError:
                    continue
        
        # If we couldn't get a location, return a default
        gps.close()
        return "Unknown", "Unknown"
    except Exception as e:
        print(f"GPS error: {e}")
        return "Unknown", "Unknown"

def send_email():
    """Send GPS location via email."""
    try:
        lat, lon = get_gps_location()
        google_maps_link = f"https://www.google.com/maps?q={lat},{lon}"
        
        subject = "? Emergency Alert: Blind Person Needs Help"
        body = f"""
        Emergency Alert! The blind person has triggered the emergency button.
        
        ?? Current Location:  
        Latitude: {lat}  
        Longitude: {lon}  
        ?? View Location on Map: {google_maps_link}

        Please take immediate action!
        """
        
        yag = yagmail.SMTP(EMAIL_SENDER, EMAIL_PASSWORD)
        yag.send(to=EMAIL_RECEIVER, subject=subject, contents=body)
        print("Email Sent Successfully!")
        speak_text("Emergency alert sent successfully")
    except Exception as e:
        print(f"Email error: {e}")
        speak_text("Failed to send emergency alert")

def run_navigation():
    """Continuously captures images and processes navigation instructions."""
    try:
        # Initialize camera here to ensure it's in the correct process
        camera = initialize_camera()
        print("Navigation system started")
        speak_text("Navigation system ready")
        
        while True:
            image_path = capture_image(camera)
            navigation_text = get_navigation_instructions(image_path)
            speak_text(navigation_text)
            time.sleep(5)  # Adjust delay based on walking speed
    except Exception as e:
        print(f"Navigation error: {e}")
        speak_text("Navigation system encountered an error")



def check_button():
    """Monitor button press and send email when pressed."""
    print("Emergency button monitoring started")
    speak_text("Emergency button is ready")
    
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            print("Button Pressed! Sending GPS Location via Email...")
            speak_text("Emergency button pressed, sending alert")
            send_email()
            time.sleep(10)  # Prevent multiple triggers
        time.sleep(0.1)  # Small delay to reduce CPU usage

if __name__ == "__main__":
    try:
        # Start the navigation and emergency button processes
        nav_process = multiprocessing.Process(target=run_navigation)
        button_process = multiprocessing.Process(target=check_button)
        
        nav_process.start()
        button_process.start()
        
        # Keep the main script running and handle Ctrl+C gracefully
        nav_process.join()
        button_process.join()
        
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
        # Clean up
        nav_process.terminate() if 'nav_process' in locals() else None
        button_process.terminate() if 'button_process' in locals() else None
        GPIO.cleanup()
    except Exception as e:
        print(f"Main program error: {e}")
        # Clean up
        if 'nav_process' in locals():
            nav_process.terminate()
        if 'button_process' in locals():
            button_process.terminate()
        GPIO.cleanup()

