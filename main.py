import speech_recognition as sr
import pyttsx3
import networkx as nx
import os

# Initialize modules
engine = pyttsx3.init()
recognizer = sr.Recognizer()

# Create indoor map
G = nx.Graph()

G.add_edges_from([
    ("Entrance", "Corridor A"),
    ("Corridor A", "Hall"),

    ("Hall", "Deep Learning Lab"),
    ("Hall", "ARVR Lab"),
    ("Hall", "DBMS Lab"),
    ("Hall", "OOPS Lab"),

    ("Hall", "Classroom 1"),
    ("Hall", "Classroom 2"),
    ("Hall", "Classroom 3"),

    ("Hall", "Restroom"),
    ("Hall", "Auditorium"),
    ("Hall", "Emergency Exit"),

    ("Hall", "Staff Hall 1"),
    ("Staff Hall 1", "Staff Hall 2"),
    ("Staff Hall 2", "HOD Office")
])

# Destination keywords
destination_keywords = {
    "Deep Learning Lab": ["deep learning lab", "dl lab"],
    "ARVR Lab": ["arvr lab", "vr lab"],
    "DBMS Lab": ["dbms lab"],
    "OOPS Lab": ["oops lab"],
    "Classroom 1": ["classroom 1"],
    "Classroom 2": ["classroom 2"],
    "Classroom 3": ["classroom 3"],
    "Staff Hall 1": ["staff hall 1"],
    "Staff Hall 2": ["staff hall 2"],
    "HOD Office": ["hod office"],
    "Restroom": ["restroom", "washroom", "toilet"],
    "Auditorium": ["auditorium"],
    "Emergency Exit": ["emergency exit", "exit"]
}

# Video mapping
video_map = {
    "Deep Learning Lab": "deep_learning_lab.mp4",
    "ARVR Lab": "arvr_lab.mp4",
    "DBMS Lab": "dbms_lab.mp4",
    "OOPS Lab": "oops_lab.mp4",
    "Classroom 1": "classroom1.mp4",
    "Classroom 2": "classroom2.mp4",
    "Classroom 3": "classroom3.mp4",
    "Staff Hall 1": "staff_hall_1.mp4",
    "Staff Hall 2": "staff_hall_2.mp4",
    "HOD Office": "hod_office.mp4",
    "Restroom": "restroom.mp4",
    "Auditorium": "auditorium.mp4",
    "Emergency Exit": "emergency_exit.mp4"
}

def speak(text):
    print(text)
    engine.say(text)
    engine.runAndWait()

def extract_destination(text):

    text = text.lower()

    for location, keywords in destination_keywords.items():

        for word in keywords:

            if word in text:
                return location

    return None

def play_video(destination):

    if destination in video_map:

        video_path = os.path.join("videos", video_map[destination])

        if os.path.exists(video_path):
            os.startfile(video_path)

print("System Ready. Speak your destination...")

with sr.Microphone() as source:
    audio = recognizer.listen(source)

try:
    text = recognizer.recognize_google(audio)

    print("You said:", text)

    destination = extract_destination(text)

    if destination:

        path = nx.shortest_path(G, source="Entrance", target=destination)

        response = "The shortest path is " + " then ".join(path)

        speak(response)

        play_video(destination)

    else:
        speak("Destination not found in map")

except:
    speak("Sorry, I could not understand")