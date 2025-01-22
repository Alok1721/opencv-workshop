import socket
import threading
import json

def start_server(teams,scores,correct_result):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 12345))
    server.listen(5)
    print("Server started, waiting for connections...")
    while True:
        conn, addr = server.accept()
        print(f"Connected by {addr}")
        threading.Thread(target=handle_client, args=(conn, addr,scores,teams,correct_result), daemon=True).start()

def handle_client(conn, addr, scores, teams,correct_result):
    try:
        # Receive the team name first (team name is sent before the result)
        team_data = conn.recv(1024).decode("utf-8")
        print(f"Received team name: {team_data}")

        try:
            received_data = json.loads(team_data)
            team_name = received_data.get("name")
            team_result = received_data.get("result")
            # Add the team if it's not already in the list
            if team_name not in teams:
                teams.append(team_name)
                scores[team_name] = 0

            print(f"Team {team_name} added. Current score: {scores[team_name]}")
            while True:
                result_data = conn.recv(1024).decode("utf-8")
                if not result_data:
                    break # Exit if no more data is received

                try:
                    # Parse the received result data
                    received_data = json.loads(result_data)
                    team_name = received_data.get("name")
                    team_result = received_data.get("result")

                    # Compare with correct_result and update score
                    if team_result == correct_result:
                        scores[team_name] += 10
                        print(f"Team {team_name} scored 10 points. Current score: {scores[team_name]}")
                    new_data_received = True
                except json.JSONDecodeError:
                    print("Error decoding the result data.")
                except Exception as e:
                    print(f"Error processing data: {e}")
        except json.JSONDecodeError:
            print(f"Error decoding the team data: {json.JSONDecodeError}")

    finally:
        # Always close the connection after processing
        conn.close()
