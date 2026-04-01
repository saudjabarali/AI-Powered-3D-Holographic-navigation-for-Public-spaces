import speech_recognition as sr
import pyttsx3
import networkx as nx
import os
import time
import threading
import tkinter as tk

# ──────────────────────────────────────────────
# IMPROVEMENT 5 — Pre-load and warm up TTS engine
# ──────────────────────────────────────────────
engine = pyttsx3.init()
engine.setProperty('rate', 150)       # slightly slower = clearer for examiners
engine.setProperty('volume', 1.0)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # change index to 1 for female voice
engine.say(" ")                        # silent warm-up call to avoid first-time stutter
engine.runAndWait()

recognizer = sr.Recognizer()

# ──────────────────────────────────────────────
# Indoor map graph (unchanged)
# ──────────────────────────────────────────────
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

# ──────────────────────────────────────────────
# Destination keywords (unchanged)
# ──────────────────────────────────────────────
destination_keywords = {
    "Deep Learning Lab": ["deep learning lab", "dl lab"],
    "ARVR Lab":          ["arvr lab", "vr lab"],
    "DBMS Lab":          ["dbms lab"],
    "OOPS Lab":          ["oops lab"],
    "Classroom 1":       ["classroom 1"],
    "Classroom 2":       ["classroom 2"],
    "Classroom 3":       ["classroom 3"],
    "Staff Hall 1":      ["staff hall 1"],
    "Staff Hall 2":      ["staff hall 2"],
    "HOD Office":        ["hod office"],
    "Restroom":          ["restroom", "washroom", "toilet"],
    "Auditorium":        ["auditorium"],
    "Emergency Exit":    ["emergency exit", "exit"]
}

# ──────────────────────────────────────────────
# Video mapping (unchanged)
# ──────────────────────────────────────────────
video_map = {
    "Deep Learning Lab": "deep_learning_lab.mp4",
    "ARVR Lab":          "arvr_lab.mp4",
    "DBMS Lab":          "dbms_lab.mp4",
    "OOPS Lab":          "oops_lab.mp4",
    "Classroom 1":       "classroom1.mp4",
    "Classroom 2":       "classroom2.mp4",
    "Classroom 3":       "classroom3.mp4",
    "Staff Hall 1":      "staff_hall_1.mp4",
    "Staff Hall 2":      "staff_hall_2.mp4",
    "HOD Office":        "hod_office.mp4",
    "Restroom":          "restroom.mp4",
    "Auditorium":        "auditorium.mp4",
    "Emergency Exit":    "emergency_exit.mp4"
}

# ──────────────────────────────────────────────
# IMPROVEMENT 1 — tkinter status display window
# Shows what was heard, destination, and path on screen
# Runs in a separate thread so it doesn't block audio
# ──────────────────────────────────────────────
def show_status(heard, destination, path):
    def _build():
        root = tk.Tk()
        root.title("Indoor Navigation System")
        root.configure(bg="black")
        root.geometry("660x220")
        root.resizable(False, False)

        tk.Label(
            root,
            text=f"Heard:  \"{heard}\"",
            fg="cyan", bg="black",
            font=("Arial", 13)
        ).pack(anchor="w", padx=20, pady=(18, 4))

        tk.Label(
            root,
            text=f"Destination:  {destination}",
            fg="#00FF88", bg="black",
            font=("Arial", 15, "bold")
        ).pack(anchor="w", padx=20, pady=4)

        path_str = "  →  ".join(path)
        tk.Label(
            root,
            text=f"Path:  {path_str}",
            fg="white", bg="black",
            font=("Arial", 12),
            wraplength=620,
            justify="left"
        ).pack(anchor="w", padx=20, pady=4)

        tk.Label(
            root,
            text="Launching holographic display...",
            fg="#FFA500", bg="black",
            font=("Arial", 11, "italic")
        ).pack(anchor="w", padx=20, pady=(8, 0))

        root.after(8000, root.destroy)  # auto-close after 8 seconds
        root.mainloop()

    # Run in a background thread so voice playback isn't blocked
    t = threading.Thread(target=_build, daemon=True)
    t.start()


# ──────────────────────────────────────────────
# Core helpers
# ──────────────────────────────────────────────
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

# ──────────────────────────────────────────────
# IMPROVEMENT 3 — Hologram sync delay before video
# The 2.5 s gap gives you time to tap play on the
# Winzo 5D Displayer app so both displays start together
# ──────────────────────────────────────────────
def play_video(destination):
    if destination in video_map:
        video_path = os.path.join("videos", video_map[destination])
        if os.path.exists(video_path):
            speak("Launching holographic display.")
            time.sleep(2.5)          # <-- tap play on Winzo app during this gap
            os.startfile(video_path) # monitor video starts right after
        else:
            speak(f"Video file for {destination} not found.")

# ──────────────────────────────────────────────
# IMPROVEMENT 2 — Main loop (keeps running until "quit")
# IMPROVEMENT 4 — adjust_for_ambient_noise before every listen
# ──────────────────────────────────────────────
print("System Ready.")
speak("Indoor navigation system ready. Say your destination.")

while True:
    try:
        with sr.Microphone() as source:
            # Improvement 4: calibrate for background noise each loop
            print("\nCalibrating for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
            speak("Please say your destination.")
            print("Listening...")
            audio = recognizer.listen(source, timeout=7, phrase_time_limit=6)

        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")

        # Exit command
        if "quit" in text.lower() or "exit" in text.lower():
            speak("Shutting down navigation system. Goodbye.")
            break

        destination = extract_destination(text)

        if destination:
            path = nx.shortest_path(G, source="Entrance", target=destination)
            response = "The shortest path is " + " then ".join(path)

            # Improvement 1: show the status window on screen
            show_status(heard=text, destination=destination, path=path)

            # Speak the path (window is already open in background thread)
            speak(response)

            # Improvement 3: sync delay then play monitor video
            play_video(destination)

        else:
            speak("Destination not recognised. Please try again.")

    # Improvement 2: handle specific errors cleanly instead of bare except
    except sr.WaitTimeoutError:
        speak("I didn't hear anything. Please try again.")

    except sr.UnknownValueError:
        speak("Sorry, I could not understand that. Please speak clearly.")

    except sr.RequestError as e:
        print(f"Speech recognition service error: {e}")
        speak("Speech recognition service is unavailable. Check your internet connection.")

    except KeyboardInterrupt:
        speak("Navigation system stopped.")
        break