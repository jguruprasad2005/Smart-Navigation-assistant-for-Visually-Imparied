import time
from picamera2 import Picamera2
import requests
import json
import pyttsx3
import base64
import os

# Initialize camera
camera = Picamera2()
camera_config = camera.create_still_configuration(main={"size": (640, 480)})
camera.configure(camera_config)
camera.start()

# Initialize text-to-speech engine
# Initialize text-to-speech engine with better settings
engine = pyttsx3.init()
engine.setProperty('rate', 130)     # Even slower for better clarity
engine.setProperty('volume', 1.0)   # Maximum volume
engine.setProperty('voice', 'english')  # Ensure English voice



# Set a higher quality voice if available
voices = engine.getProperty('voices')
for voice in voices:
    if "english" in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break



def capture_image():
    """Capture an image and save it"""
    filename = '/home/gurup/blind_navigation/test.jpg'
    camera.capture_file(filename)
    print(f"Image saved to {filename}")
    return filename

def get_navigation_instructions(image_path):
    """Send image to Google Gemini API for navigation instructions"""
    print("Processing image for navigation instructions...")
    import google.generativeai as genai
    from PIL import Image
    
    # Configure the API
    genai.configure(api_key="YOUR API KEY")
    
    # Load the image
    image = Image.open(image_path)
    
    # Set up the model
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    # Create a clearer prompt that won't be repeated in the response
    prompt = """
    RESPOND ONLY WITH NAVIGATION DIRECTIONS. NO PREAMBLE.
    
    Analyze this image for a blind person navigation system. 
    Provide ONLY 2-3 very short sentences with:
    - Clear path direction
    - Immediate obstacles
    - Simple directional terms
    - Distances in steps
    
    DO NOT start with "I see" or repeat these instructions.
    """
    
    # Generate content with the image
    response = model.generate_content([prompt, image])
    
    # Extract just the response text
    navigation_text = response.text()
    
    # Clean up the response
    #navigation_text = clean_response(navigation_text)
    
    print(f"Navigation instructions: {navigation_text}")
    return navigation_text

def speak_text(text):
    """Convert text to speech and play it"""
    print(f"Speaking: {text}")
    engine.say(text)
    engine.runAndWait()
    print("Speech completed")

# Main loop
try:
    while True:
        # Capture image
        image_path = capture_image()
        
        # Get navigation instructions
        navigation_text = get_navigation_instructions(image_path)
        
        # Speak the navigation instructions
        speak_text(navigation_text)
        
        # Wait before the next capture
        time.sleep(3)  # Adjust timing based on walking speed
        
except KeyboardInterrupt:
    print("Program terminated by user")