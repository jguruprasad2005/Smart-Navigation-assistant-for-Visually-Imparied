import time
from picamera2 import Picamera2
import requests
import json
import subprocess
import pyttsx3
import base64
import os
from gtts import gTTS
from playsound import playsound

# Initialize camera
camera = Picamera2()
camera_config = camera.create_still_configuration(main={"size": (640, 480)})
camera.configure(camera_config)
camera.start()


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
    You are a navigation assistant for a blind person. Your goal is to provide *detailed* and *clear* descriptions
    
    Describe the overall scene: Mention what objects, people, or obstacles are present in the image.
    Give clear navigation guidance:Specify directions (left, right, straight, stop), approximate distances, and any potential risks.
    Include safety precautions: Mention any moving objects, steps, slopes, or uneven surfaces.  
    Ensure clarity: Use natural, conversational language that is easy to understand.
    
    DO NOT start with "I see" or repeat these instructions.
    """
    
    # Generate content with the image
    response = model.generate_content([prompt, image])
    
    # Extract just the response text
    navigation_text = response.text
    
    # Clean up the response
    #navigation_text = clean_response(navigation_text)
    
    print(f"Navigation instructions: {navigation_text}")
    return navigation_text

def speak_text(text):
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save("output.mp3")
        #os.system(" mpg321 output.mp3 ")
        subprocess.run(["ffplay", "-nodisp", "-autoexit", "-af", "atempo=1.5", "output.mp3"], 
                      stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        #os.remove("output.mp3")
    except Exception as e:
        print(f"TTS error: {e}")
        # Fallback to simpler method if TTS fails
        os.system(f'echo "{text}" | festival --tts')

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
