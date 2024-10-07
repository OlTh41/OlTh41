import socket
import pickle
import pyautogui
 
# Create the client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("172.16.115.143", 5000))  # Connect to your updated IP address
 
running = True
while running:
    try:
        # Receive the data (mouse coordinates)
        data = client_socket.recv(1024)
        if not data:
            break
        mouse_pos = pickle.loads(data)  # Deserialize the data
        print(f"Received coordinates: {mouse_pos}")
        # Simulate left-click at the received position on the client
        pyautogui.click(mouse_pos[0], mouse_pos[1])
    except Exception as e:
        print(f"Error: {e}")
        running = False
 
# Close the connection
client_socket.close()