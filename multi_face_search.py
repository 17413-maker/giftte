import cv2
import requests
from PIL import Image
from io import BytesIO
import numpy as np
import os
import webbrowser
import base64
import urllib.parse

# Load image from file or URL
def load_image(path_or_url):
    if path_or_url.startswith("http"):
        resp = requests.get(path_or_url)
        img = Image.open(BytesIO(resp.content)).convert('RGB')
        return np.array(img)[:, :, ::-1]  # RGB to BGR for OpenCV
    else:
        return cv2.imread(path_or_url)

# Detect faces using Haar Cascades
def detect_faces(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    face_images = []
    for i, (x, y, w, h) in enumerate(faces):
        face = image[y:y+h, x:x+w]
        face_images.append(face)
        filename = f"face_{i+1}.jpg"
        cv2.imwrite(filename, face)
        print(f"Saved {filename}")
    return face_images

# Encode image to base64 for upload (Google reverse image search)
def image_to_data_url(image_path):
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    b64_data = base64.b64encode(img_bytes).decode()
    return f"data:image/jpeg;base64,{b64_data}"

# Open Google reverse image search in browser automatically
def reverse_image_search(face_images):
    for i, _ in enumerate(face_images):
        filename = f"face_{i+1}.jpg"
        # Use Google reverse image search by uploading file (opens browser)
        query_url = f"https://www.google.com/searchbyimage?&image_url=file://{urllib.parse.quote(os.path.abspath(filename))}"
        print(f"Opening browser for face {i+1}")
        webbrowser.open(query_url)

# ------------------- Main -------------------
image_path_or_url = "example.jpg"  # Replace with your file path or URL

# Load image
image = load_image(image_path_or_url)

# Detect and crop faces
faces = detect_faces(image)

# Run automated reverse image search
reverse_image_search(faces)

