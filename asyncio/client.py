import asyncio
import websockets
import cv2
import base64
import json
import numpy as np
import threading

class VideoChatClient:
    def __init__(self, uri="ws://localhost:8765"):
        self.uri = uri
        self.running = True
        
    def get_input(self):
        while self.running:
            message = input()
            if message.lower() == 'quit':
                self.running = False
                break
            self.message_queue.put_nowait(message)

    async def connect(self):
        self.message_queue = asyncio.Queue()
        
        # Start input thread
        input_thread = threading.Thread(target=self.get_input)
        input_thread.daemon = True
        input_thread.start()
        
        print(f"Connecting to {self.uri}")
        async with websockets.connect(self.uri) as websocket:
            print("Connected! Type messages and press Enter to send. Type 'quit' to exit.")
            
            # Create video window
            cv2.namedWindow("Stream", cv2.WINDOW_NORMAL)
            
            while self.running:
                try:
                    # Handle sending messages
                    try:
                        message = self.message_queue.get_nowait()
                        packet = json.dumps({
                            "type": "message",
                            "content": message
                        })
                        await websocket.send(packet)
                    except asyncio.QueueEmpty:
                        pass
                    
                    # Handle receiving data
                    try:
                        data = await asyncio.wait_for(websocket.recv(), timeout=0)
                        packet = json.loads(data)
                        
                        if packet["type"] == "video":
                            # Handle video frame
                            frame_data = base64.b64decode(packet["frame"])
                            frame_arr = np.frombuffer(frame_data, dtype=np.uint8)
                            frame = cv2.imdecode(frame_arr, flags=cv2.IMREAD_COLOR)
                            cv2.imshow("Stream", frame)
                            if cv2.waitKey(1) & 0xFF == ord('q'):
                                break
                        elif packet["type"] == "message":
                            # Handle chat message
                            print(f"Client-{packet['sender']}: {packet['content']}")
                            
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        print(f"Error: {e}")
                        break
                        
                except Exception as e:
                    print(f"Error: {e}")
                    break
                    
            cv2.destroyAllWindows()
            self.running = False

if __name__ == "__main__":
    client = VideoChatClient()  # Change uri if needed
    asyncio.run(client.connect())
