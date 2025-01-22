import asyncio
import websockets
import cv2
import base64
import json
import socket

# UDP socket for video streaming
UDP_IP = "0.0.0.0"
UDP_PORT = 5000
BUFFER_SIZE = 65536

clients = {}

async def handle_client(websocket, path):
    try:
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "login":
                nickname = data["nickname"]
                clients[nickname] = websocket
                await broadcast_users_list()
                print(f"{nickname} connected")

            elif data["type"] == "message":
                sender = data["nickname"]
                chat_message = data["content"]
                print(f"Chat: {sender}: {chat_message}")
                await broadcast_message(sender, chat_message)

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
        for name, ws in list(clients.items()):
            if ws == websocket:
                del clients[name]
                break
        await broadcast_users_list()

async def broadcast_users_list():
    users_list = json.dumps({"type": "users_list", "users": list(clients.keys())})
    await asyncio.wait([ws.send(users_list) for ws in clients.values()])

async def broadcast_message(sender, message):
    packet = json.dumps({"type": "message", "sender": sender, "content": message})
    await asyncio.wait([ws.send(packet) for ws in clients.values()])

async def udp_video_stream():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((UDP_IP, UDP_PORT))
    print(f"UDP server listening on port {UDP_PORT}")

    while True:
        frame, client_addr = udp_socket.recvfrom(BUFFER_SIZE)
        for name, ws in clients.items():
            try:
                frame_data = json.dumps({"type": "video", "frame": base64.b64encode(frame).decode('utf-8')})
                await ws.send(frame_data)
            except Exception as e:
                print(f"Error sending video to {name}: {e}")

async def main():
    ws_server = await websockets.serve(handle_client, "0.0.0.0", 8765)
    print("WebSocket server listening on ws://0.0.0.0:8765")
    await asyncio.gather(ws_server.wait_closed(), udp_video_stream())

if __name__ == "__main__":
    asyncio.run(main())
