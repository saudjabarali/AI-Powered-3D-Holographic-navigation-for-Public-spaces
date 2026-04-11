import speech_recognition as sr
import pyttsx3
import networkx as nx
import os
import time
import threading
import tkinter as tk
import matplotlib
matplotlib.use("TkAgg")          # must be set before importing pyplot
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

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
# Fixed node positions — laid out to match the
# real building map (Entrance at bottom, Hall in
# centre, rooms fanning out around it)
# ──────────────────────────────────────────────
NODE_POS = {
    "Entrance":         (4.0,  0.0),
    "Corridor A":       (4.0,  1.2),
    "Hall":             (4.0,  2.5),

    # Labs — left side
    "Deep Learning Lab":(0.5,  3.8),
    "ARVR Lab":         (1.8,  3.8),
    "DBMS Lab":         (3.1,  3.8),
    "OOPS Lab":         (4.4,  3.8),

    # Classrooms — right side
    "Classroom 1":      (5.7,  3.8),
    "Classroom 2":      (7.0,  3.8),
    "Classroom 3":      (8.3,  3.8),

    # Facilities — far right of Hall row
    "Restroom":         (6.5,  2.5),
    "Auditorium":       (7.8,  2.5),
    "Emergency Exit":   (9.1,  2.5),

    # Staff corridor — left of Hall row
    "Staff Hall 1":     (1.8,  2.5),
    "Staff Hall 2":     (0.5,  2.5),
    "HOD Office":       (0.5,  1.2),
}

# Colour scheme used in the map
_C_DEFAULT  = "#2C3E50"   # dark slate  — unvisited nodes
_C_PATH     = "#E74C3C"   # red         — nodes on the route
_C_START    = "#27AE60"   # green       — Entrance
_C_END      = "#F39C12"   # amber       — destination
_C_EDGE     = "#7F8C8D"   # grey        — normal edges
_C_EDGE_ACT = "#E74C3C"   # red         — active path edges
_C_BG       = "#1A1A2E"   # very dark   — figure background
_C_LABEL    = "white"


def show_map(path):
    """
    Draw the full building graph and highlight the computed route.
    Runs in a background thread so it never blocks audio or the
    status window.  The figure auto-closes after 10 seconds.
    """
    def _draw():
        path_set   = set(path)
        path_edges = list(zip(path, path[1:]))

        # ── node colours ──────────────────────────────────────────
        node_colors = []
        for node in G.nodes():
            if node == "Entrance":
                node_colors.append(_C_START)
            elif node == path[-1]:
                node_colors.append(_C_END)
            elif node in path_set:
                node_colors.append(_C_PATH)
            else:
                node_colors.append(_C_DEFAULT)

        # ── edge colours & widths ─────────────────────────────────
        edge_colors = []
        edge_widths = []
        for edge in G.edges():
            if edge in path_edges or tuple(reversed(edge)) in path_edges:
                edge_colors.append(_C_EDGE_ACT)
                edge_widths.append(3.5)
            else:
                edge_colors.append(_C_EDGE)
                edge_widths.append(1.2)

        # ── figure ───────────────────────────────────────────────
        fig, ax = plt.subplots(figsize=(13, 6))
        fig.patch.set_facecolor(_C_BG)
        ax.set_facecolor(_C_BG)
        ax.set_title(
            f"Navigation  ▶  Entrance  →  {path[-1]}",
            color="white", fontsize=13, fontweight="bold", pad=12
        )
        ax.axis("off")

        nx.draw_networkx(
            G,
            pos=NODE_POS,
            ax=ax,
            node_color=node_colors,
            edge_color=edge_colors,
            width=edge_widths,
            node_size=700,
            font_size=7.5,
            font_color=_C_LABEL,
            font_weight="bold",
            arrows=False,
        )

        # ── legend ───────────────────────────────────────────────
        legend_items = [
            mpatches.Patch(color=_C_START,   label="Start (Entrance)"),
            mpatches.Patch(color=_C_END,     label=f"Destination ({path[-1]})"),
            mpatches.Patch(color=_C_PATH,    label="Route"),
            mpatches.Patch(color=_C_DEFAULT, label="Other rooms"),
        ]
        ax.legend(
            handles=legend_items,
            loc="lower left",
            facecolor="#2C3E50",
            edgecolor="white",
            labelcolor="white",
            fontsize=8,
        )

        # ── path text strip at bottom ─────────────────────────────
        path_text = "  →  ".join(path)
        fig.text(
            0.5, 0.02, path_text,
            ha="center", va="bottom",
            color="#ECF0F1", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#2C3E50",
                      edgecolor="#E74C3C", linewidth=1.5)
        )

        plt.tight_layout(rect=[0, 0.06, 1, 1])

        # auto-close after 10 s without user interaction
        timer = fig.canvas.new_timer(interval=10_000)
        timer.add_callback(plt.close, fig)
        timer.start()

        plt.show()   # blocks this thread only — other threads run freely

    t = threading.Thread(target=_draw, daemon=True)
    t.start()


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
# ADB HOLOGRAM SYNC
#
# The Winzo 5D Displayer app shows a numbered video list.
# Each destination maps to a specific row in that list.
# ADB taps the correct row automatically when a destination
# is spoken — both the monitor video and hologram fan
# start at exactly the same moment.
#
# HOW TO SET UP (one-time, ~10 minutes):
#
#   1. Install ADB on Windows:
#      Open PowerShell and run:
#        winget install Google.PlatformTools
#      Restart VS Code after so PATH is updated.
#      Verify with:  adb version
#
#   2. Enable USB Debugging on your phone:
#      Settings → About Phone → tap Build Number 7 times
#      → Developer Options → enable USB Debugging
#
#   3. Connect phone to laptop via USB data cable.
#      Accept the "Allow USB Debugging?" popup on your phone.
#      Verify with:  adb devices
#      (should show one device, not "unauthorized")
#
#   4. Calibrate row Y-coordinates (if rows don't tap right):
#      Your screen resolution may differ slightly from the
#      values pre-filled below. Run this to get exact coords:
#
#        adb shell getevent -l
#
#      Then physically tap each row in the Winzo app one by one.
#      Read the ABS_MT_POSITION_Y hex value, convert to decimal,
#      and update the Y values in WINZO_TAP_COORDS below.
#      X stays at 360 (horizontal centre) for all rows.
#
#   5. Test with the calibration mode:
#      Set RUN_TAP_CALIBRATION = True, run the script,
#      say a destination — watch the correct row get tapped.
#      Then set RUN_TAP_CALIBRATION = False.
#
# ──────────────────────────────────────────────
# YOUR APP VIDEO LIST (from screenshot):
#   01.ARVRLAB      02.AUDITORM     03.CLSROOM1
#   04.CLSROOM2     05.CLSROOM3     06.DBMSLAB
#   07.DLLAB        08.EMRGNCY      09.HODOFFIC
#   10.OOPSLAB      11.RESTROOM     12.STFHALL1
#   13.STFHALL2
# ──────────────────────────────────────────────

import subprocess

# ── CALIBRATION MODE ────────────────────────────
# Set True to test tap coordinates, False for normal use
RUN_TAP_CALIBRATION = False
CALIBRATION_DESTINATION = "ARVR Lab"   # destination to test when calibrating
# ────────────────────────────────────────────────

# ── ROW TAP COORDINATES ─────────────────────────
# X = 360  (horizontal centre of screen, same for every row)
# Y values calculated from your screenshot:
#   Header bar ends ~148px. Row height ≈ 88px.
#   Row N centre  =  148 + (N-1)*88 + 44
#
#   Row 1 → Y = 192    Row 2 → Y = 280    Row 3 → Y = 368
#   Row 4 → Y = 456    Row 5 → Y = 544    Row 6 → Y = 632
#   Row 7 → Y = 720    Row 8 → Y = 808    Row 9 → Y = 896
#   Row 10 → Y = 984   Row 11 → Y = 1072  Row 12 → Y = 1160
#   Row 13 → Y = 1248
#
# If your phone has a different resolution, adjust the Y values
# using:  adb shell getevent -l  (see Step 4 above)
# ────────────────────────────────────────────────
WINZO_TAP_COORDS = {
    # destination name       -> (X,   Y)   from Android 11 pointer location
    "Welcome":               (111,  205),  # 01.AAWELCOME
    "ARVR Lab":              (104,  286),  # 02.ARVRLAB
    "Auditorium":            (128,  391),  # 03.AUDITORM
    "Classroom 1":           (137,  492),  # 04.CLSROOM1
    "Classroom 2":           (135,  600),  # 05.CLSROOM2
    "Classroom 3":           (145,  692),  # 06.CLSROOM3
    "DBMS Lab":              (147,  798),  # 07.DBMSLAB
    "Deep Learning Lab":     (126,  876),  # 08.DLLAB
    "Emergency Exit":        (123,  961),  # 09.EMRGNCY
    "HOD Office":            (148, 1065),  # 10.HODOFFIC
    "OOPS Lab":              (124, 1165),  # 11.OOPSLAB
    "Restroom":              (165, 1253),  # 12.RESTROOM
    "Staff Hall 1":          (132, 1191),  # 13.STFHALL1 (after scroll)
    "Staff Hall 2":          (123, 1286),  # 14.STFHALL2 (after scroll)
}
# NOTE: Hall, Corridor A, and Entrance have no hologram video
# so they are not in the list — that's correct.


def _adb_check():
    """Returns True if ADB can see a connected device, False otherwise."""
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True, text=True, timeout=3
        )
        lines = [l.strip() for l in result.stdout.splitlines()
                 if l.strip() and "List of devices" not in l]
        return any("device" in l for l in lines)
    except FileNotFoundError:
        return False   # adb not installed
    except Exception:
        return False


# ── Winzo package name ──────────────────────────
# Find yours by running:  adb shell pm list packages | findstr -i 5d
# Then paste the result here e.g. "com.example.5ddisplayer"
WINZO_PACKAGE = "com.zxb.yf.Z3"   # most common 5D displayer package name
# ─────────────────────────────────────────────────


def _adb_tap(destination):
    """
    1. Brings the Winzo app to the foreground (so the tap lands on it)
    2. Waits a moment for the app to appear
    3. Taps the correct video row
    Runs in a background thread so it never blocks audio.
    """
    if destination not in WINZO_TAP_COORDS:
        print(f"[ADB] No tap coords for '{destination}' — skipping fan trigger.")
        return

    x, y = WINZO_TAP_COORDS[destination]

    def _do_tap():
        try:
            # Step 1 — bring Winzo to foreground
            subprocess.run(
                ["adb", "shell", "monkey", "-p", WINZO_PACKAGE,
                 "-c", "android.intent.category.LAUNCHER", "1"],
                timeout=4, capture_output=True
            )
            # Step 2 — wait for app to appear on screen
            time.sleep(1.5)

            # Step 3 — tap the correct row
            subprocess.run(
                ["adb", "shell", "input", "tap", str(x), str(y)],
                timeout=3, capture_output=True
            )
            print(f"[ADB] Tapped '{destination}' row at ({x}, {y}) in Winzo app.")
        except FileNotFoundError:
            print("[ADB] adb not found — is Google Platform Tools installed?")
        except Exception as e:
            print(f"[ADB] Tap failed: {e}")

    threading.Thread(target=_do_tap, daemon=True).start()


# ── Startup check ────────────────────────────────
_ADB_READY = _adb_check()
if _ADB_READY:
    print("[ADB] Phone detected ✓  Hologram fan will sync automatically.")
else:
    print("[ADB] No phone detected — check USB cable & USB Debugging.")
    print("      Hologram fan will NOT be auto-triggered this session.")

# ── Calibration helper ───────────────────────────
if RUN_TAP_CALIBRATION and _ADB_READY:
    dest = CALIBRATION_DESTINATION
    x, y = WINZO_TAP_COORDS.get(dest, (360, 192))
    print(f"\n[CALIBRATION] Testing tap for '{dest}' → ({x}, {y}) in 3 seconds...")
    print("              Watch your phone — the correct row should be tapped.")
    time.sleep(3)
    _adb_tap(dest)
    time.sleep(1)
    print("[CALIBRATION] Done.")
    print("              If the wrong row was tapped, adjust its Y value in")
    print("              WINZO_TAP_COORDS and run again.")
    print("              If correct, set RUN_TAP_CALIBRATION = False.\n")


# Destinations that need a scroll before tapping (not visible on first screen)
NEEDS_SCROLL = {"Staff Hall 1", "Staff Hall 2"}


def _adb_run(cmd):
    """Run a single adb shell command and wait for it."""
    subprocess.run(["adb", "shell"] + cmd.split(),
                   timeout=3, capture_output=True)


def _tap_welcome():
    """
    Taps the welcome video row in Winzo so the hologram fan
    returns to the looping welcome screen after each destination.
    Scrolls back to top first to make sure row 01 is visible.
    Runs in a background thread so it never blocks anything.
    """
    def _do():
        # Scroll back to top so welcome row is visible
        _adb_run("input swipe 400 400 400 800 300")
        time.sleep(0.4)
        subprocess.run(
            ["adb", "shell", "input", "tap",
             str(WINZO_TAP_COORDS["Welcome"][0]),
             str(WINZO_TAP_COORDS["Welcome"][1])],
            timeout=3, capture_output=True
        )
        print("[ADB] Returned hologram fan to Welcome screen")
    threading.Thread(target=_do, daemon=True).start()


def play_video(destination):
    """
    Sequence:
      1. ADB tap fires FIRST (before anything else) — no thread, no delay
      2. Terminal shows the row number as confirmation
      3. Voice says "Launching holographic display"
      4. Monitor video plays
      5. Background thread waits for video to end then taps Welcome
    """
    if destination not in video_map:
        return

    video_path = os.path.join("videos", video_map[destination])
    if not os.path.exists(video_path):
        speak(f"Video file for {destination} not found.")
        return

    # Video duration (seconds) — update to match your actual video lengths
    VIDEO_DURATION = {
        "ARVR Lab":          9,
        "Auditorium":        7,
        "Classroom 1":       8,
        "Classroom 2":       7,
        "Classroom 3":       8,
        "DBMS Lab":          8,
        "Deep Learning Lab": 9,
        "Emergency Exit":    10,
        "HOD Office":        10,
        "OOPS Lab":          8,
        "Restroom":          6,
        "Staff Hall 1":      9,
        "Staff Hall 2":      9,
    }

    # Row number for terminal display
    row_number = {
        "ARVR Lab":          "02", "Auditorium":        "03",
        "Classroom 1":       "04", "Classroom 2":       "05",
        "Classroom 3":       "06", "DBMS Lab":          "07",
        "Deep Learning Lab": "08", "Emergency Exit":    "09",
        "HOD Office":        "10", "OOPS Lab":          "11",
        "Restroom":          "12", "Staff Hall 1":      "13",
        "Staff Hall 2":      "14",
    }
    row      = row_number.get(destination, "??")
    duration = VIDEO_DURATION.get(destination, 10)
    needs_scroll = destination in NEEDS_SCROLL

    # ── STEP 1: ADB tap fires RIGHT NOW, synchronously, before anything else ──
    # This runs before pyttsx3 touches the audio device so nothing can block it
    if _ADB_READY and destination in WINZO_TAP_COORDS:
        try:
            if needs_scroll:
                # Scroll list down first so Staff Hall rows become visible
                subprocess.run(
                    ["adb", "shell", "input", "swipe",
                     "400", "800", "400", "400", "300"],
                    timeout=4
                )
                time.sleep(0.5)

            x, y = WINZO_TAP_COORDS[destination]
            result = subprocess.run(
                ["adb", "shell", "input", "tap", str(x), str(y)],
                timeout=4, capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"[ADB] Tapped row {row} ({destination}) at ({x},{y}) OK")
            else:
                print(f"[ADB] Tap error: {result.stderr.strip()}")
        except Exception as e:
            print(f"[ADB] Tap failed: {e}")

    # ── STEP 2: Terminal prompt (confirmation for you) ─────────────────────────
    print("")
    print("=" * 42)
    print(f"  HOLOGRAM  >>  ROW {row}  —  {destination}")
    print("=" * 42)
    print("")

    # ── STEP 3 + 4: Speak then play monitor video ──────────────────────────────
    speak("Launching holographic display.")
    os.startfile(video_path)

    # ── STEP 5: After video ends, return hologram fan to welcome loop ──────────
    def _return_to_welcome():
        time.sleep(duration + 1)
        _tap_welcome()
        print("[Hologram] Returned to welcome screen")

    threading.Thread(target=_return_to_welcome, daemon=True).start()


# ──────────────────────────────────────────────
# IMPROVEMENT 2 — Main loop (keeps running until "quit")
# IMPROVEMENT 4 — adjust_for_ambient_noise before every listen
# ──────────────────────────────────────────────
print("System Ready.")
speak("Indoor navigation system ready. Say your destination.")

# Tap welcome video row at startup so hologram fan starts looping immediately
if _ADB_READY:
    time.sleep(1)
    _tap_welcome()
    print("[Hologram] Welcome screen started on hologram fan")


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

        # Exit command — only "quit" or the single word "exit" stops the system.
        # Saying "emergency exit" still navigates correctly.
        text_stripped = text.lower().strip()
        if "quit" in text_stripped or text_stripped == "exit":
            speak("Shutting down navigation system. Goodbye.")
            break

        destination = extract_destination(text)

        if destination:
            path = nx.shortest_path(G, source="Entrance", target=destination)
            response = "The shortest path is " + " then ".join(path)

            # Improvement 1: show the status window on screen
            show_status(heard=text, destination=destination, path=path)

            # Path visualisation — highlighted map pops up in background
            show_map(path)

            # Speak the path (windows are already open in background threads)
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