import socket
import time
import json


SERVER_IP = "127.0.0.1" #127.0.0.1
SERVER_PORT = 12345
test_result = [[1, 2], [3, 5], [6, 7], [5, 6]]

def start_client():
    team_name = input("Enter your team name: ")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER_IP, SERVER_PORT))
    try:
        while True:
            # Prepare the data in the desired format
            data = {
                "name": team_name,
                "result": test_result
            }
            json_data = json.dumps(data)
            client.sendall(json_data.encode("utf-8"))
            print(f"Sent data: {json_data}")
            time.sleep(2)  
    except KeyboardInterrupt:
        print("Client disconnected.")
    finally:
        client.close()

if __name__ == "__main__":
    start_client()
