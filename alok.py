import socket
import base64
import pygame
import threading
import numpy as np
import colorsys
import cv2
import json
import components

# Constants
BUFF_SIZE = 65536
host_ip = 'localhost'  # Change this to your server's IP
port = 6060
WIDTH, HEIGHT = 1000, 600
SHAPES_LIST_WIDTH = 300
VIDEO_WIDTH = WIDTH - SHAPES_LIST_WIDTH
SHAPES_LIST_HEIGHT = HEIGHT
SHAPE_OFFSET_Y = 350

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zine CV - Client")
font = pygame.font.Font(None, 28)
last_processed_frame = None
bg = pygame.image.load("score.jpg")
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
# Client state
client_socket = None
shapes_list = []
stage1_response=[]
running = True
frame_processed = False

BASIC_COLORS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "black": (0, 0, 0),
      "invalid": (255, 255, 255),
    "white": (255, 255, 255)
}

def get_simplified_color_name(hsv_color):
    """Map HSV color to red, green, blue, or invalid."""
    h, s, v = hsv_color

    if s < 0.2 or v < 0.2: #low saturation or value, invalid
        return "invalid"
    elif 0 <= h <= 20 or 160 <= h <= 180:  # Red (wraps around)
        return "red"
    elif 40 <= h <= 80:  # Green
        return "green"
    elif 100 <= h <= 140:  # Blue
        return "blue"
    else:
        return "invalid"
    
def hsv_to_rgb(hsv_color):
    """Convert HSV color to RGB."""
    h, s, v = hsv_color
    h = h/180.0
    s = s/255
    v = v/255
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))

def identify_shapes_and_colors(frame):
    """Identify shapes and colors using simplified HSV mapping."""
    global shapes_list
    shapes_list.clear()
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    color_ranges = {
        'red': [
            (np.array([0, 100, 100]), np.array([10, 255, 255])),
            (np.array([160, 100, 100]), np.array([180, 255, 255]))
        ],
        'blue': [(np.array([90, 50, 50]), np.array([130, 255, 255]))],
        'green': [(np.array([30, 50, 50]), np.array([90, 255, 255]))]

    }
    result_list = []

    for color_name, ranges in color_ranges.items():
        color_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        color_mask = cv2.GaussianBlur(color_mask, (5, 5), 0)
        kernel = np.ones((5, 5), np.uint8)
        color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel)
        for lower, upper in ranges:
            mask = cv2.inRange(hsv, lower, upper)
            color_mask = cv2.bitwise_or(color_mask, mask)

        contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            if cv2.contourArea(contour) < 50:
                continue

            M = cv2.moments(contour)
            if M["m00"] == 0:
                continue
            center_x = int(M["m10"] / M["m00"])
            center_y = int(M["m01"] / M["m00"])
            


            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
            num_vertices = len(approx)

            if num_vertices == 3:
                shape = "triangle"
            elif num_vertices == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h
                shape = "square" if 0.90 <= aspect_ratio <= 1.1 else "rectangle"
            elif num_vertices > 4:
                shape = "circle"
            else:
                continue

            result_list.append({
                'shape': shape,
                'color': color_name,
                'center_x': center_x,
                'center_y': center_y,
            })
            cv2.putText(frame, str(shape), (center_x, center_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.drawContours(frame, [approx], 0, (255, 255, 255), -1)
            x, y, w, h = cv2.boundingRect(approx)
            shapes_list.append((shape, color_name))

    return frame, result_list

def receive_message():
    global client_socket, frame_processed, last_processed_frame
    buffer = ""
    while running:
        try:
            msg = client_socket.recv(BUFF_SIZE)
            if msg:
                # buffer += msg.decode('utf-8')
                # json_data, idx = json.JSONDecoder().raw_decode(buffer)
                # json_data = json.loads(msg.decode('utf-8'))
                # print(f"[INFO] Received data: {json_data['type']} ")
                # if json_data["type"] == "result":
                #     print(f"[INFO] Received results: {json_data['score']}")
                try:
                    json_data = json.loads(msg.decode('utf-8'))
                    # print("[INFO] Received data: ", json_data)
                    if json_data['type'] == 'video_frame':
                        receive_video(json_data['frame'])
                    # elif json_data['type'] == 'result':
                    #     print(f"[INFO] Received results: {json_data['result']}")
                except json.JSONDecodeError:
                    print(f"[ERROR] Failed to decode JSON data")
                # buffer = buffer[idx:]
            else:
                print("[INFO] Connection closed by server")
                break
         
        except socket.error as e:
            print(f"[ERROR] Error receiving data from {e}")
        except Exception as e:
            print(f"[ERROR] Error: {e}")
            break
def process_and_draw(frame):
    nodes_shortest = shortest_path(frame)
    directions_creation(frame, nodes_shortest)

def receive_video(message):
    """Receive and display video stream."""
    global frame_processed, last_processed_frame
    frame_data = base64.b64decode(message)
    nparr = np.frombuffer(frame_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is not None:
        if frame_processed:
            frame,_ = identify_shapes_and_colors(frame)
            last_processed_frame = frame.copy()

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = np.rot90(frame)
        frame_surface = pygame.surfarray.make_surface(frame)
        screen.blit(frame_surface, (0, 0))

        if last_processed_frame is not None:
            processed_frame_rgb = cv2.cvtColor(last_processed_frame, cv2.COLOR_BGR2RGB)
            processed_frame_rgb = np.rot90(processed_frame_rgb)
            processed_frame_surface = pygame.surfarray.make_surface(processed_frame_rgb)

            processed_frame_x = VIDEO_WIDTH - processed_frame_surface.get_width() // 2
            screen.blit(processed_frame_surface, (processed_frame_x, 0))
            # print("\n\nshortest path\n:",shortest_path(last_processed_frame))
            # threading.Thread(target=process_and_draw,args=(last_processed_frame,), daemon=True).start()
            # nodes_shortest=shortest_path(last_processed_frame)
            # directions_creation(last_processed_frame, nodes_shortest)
            # print("Thread execution completed, proceeding further...")

        if frame_processed:
            draw_shape_list()
            frame_processed = False

        # pygame.display.update()

  

def draw_shape_list():
    """Draw the list of identified shapes."""
    pygame.draw.rect(screen, (0, 0, 0), (VIDEO_WIDTH // 2 + VIDEO_WIDTH//4, 0, SHAPES_LIST_WIDTH, SHAPES_LIST_HEIGHT))
    y_offset = SHAPE_OFFSET_Y
    for shape, color_name in shapes_list:
        shape_text = font.render(f"{shape} - {color_name}", True, components.WHITE)
        text_x = (VIDEO_WIDTH//2 + VIDEO_WIDTH//4) + (SHAPES_LIST_WIDTH // 2 - shape_text.get_width() // 2)
        screen.blit(shape_text, (text_x, y_offset))
        y_offset += 30

def send_shapes_to_server(team_name):
    """Send the current shapes list to the server."""
    global shapes_list, client_socket
    try:
        shapes_data = json.dumps({
            "team_name": team_name,
             "shapes": shapes_list})  # Convert shapes list to JSON format
        client_socket.send(shapes_data.encode('utf-8'))
        print("[INFO] Shapes list sent to server.")
    except Exception as e:
        print(f"[ERROR] Error sending shapes list: {e}")

def get_team_name():
    """Prompt the user for their team name."""
    team_name = input("Enter your team name: ")
    return team_name

def start_client():
    """Connect to the server and handle events."""
    global client_socket, running
    screen.blit(bg, (0, 0))
    team_name = get_team_name()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_thread = threading.Thread(target=receive_message, daemon=True)

    try:
        client_socket.connect((host_ip, port))
        if not client_socket:
            print("[ERROR] Failed to connect to server")
            return
        
        # client_socket.sendto("REQUEST_STREAM".encode('utf-8'), (host_ip, port))
        print("[INFO] Connected to server")
        sock_thread.start()

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if 50 <= x <= 250 and HEIGHT - 100 <= y <= HEIGHT - 50:
                        process_frame()
                    elif 300 <= x <= 500 and HEIGHT - 100 <= y <= HEIGHT - 50:
                        running = False
                    elif 550 <= x <= 750 and HEIGHT - 100 <= y <= HEIGHT - 50:  # Send Shapes button
                        send_shapes_to_server(team_name)

            # Draw buttons
            pygame.draw.rect(screen, (0, 255, 0), (50, HEIGHT - 100, 200, 50))
            pygame.draw.rect(screen, (255, 0, 0), (300, HEIGHT - 100, 200, 50))
            pygame.draw.rect(screen, (0, 0, 255), (550, HEIGHT - 100, 200, 50))  # Blue button

            process_text = font.render("Process Frame", True, (255, 255, 255))
            disconnect_text = font.render("Disconnect", True, (255, 255, 255))
            send_shapes_text = font.render("Send Shapes", True, (255, 255, 255))

            screen.blit(process_text, (50 + 100 - process_text.get_width() // 2, HEIGHT - 90))
            screen.blit(disconnect_text, (300 + 100 - disconnect_text.get_width() // 2, HEIGHT - 90))
            screen.blit(send_shapes_text, (550 + 100 - send_shapes_text.get_width() // 2, HEIGHT - 90))

            pygame.display.update()

    except Exception as e:
        print(f"[ERROR] Error: {e}")
    finally:
        if sock_thread.is_alive():
            sock_thread.join()

        if client_socket:
            client_socket.close()
        pygame.quit()
        print("[INFO] Disconnected")

def process_frame():
    """Set the flag to process the frame."""
    global frame_processed
    frame_processed = True
    print("[INFO] Processing frame...")


'''finding teh shortest path'''
def totalCost(mask, curr, n, cost, memo, parent):
    if mask == (1 << n) - 1:
        return cost[curr][start_node]
    if memo[curr][mask] != -1:
        return memo[curr][mask]
    ans = float('inf')
    next_city = -1
    for i in range(n):
        if (mask & (1 << i)) == 0:  
            temp_cost = cost[curr][i] + totalCost(mask | (1 << i), i, n, cost, memo, parent)
            if temp_cost < ans:
                ans = temp_cost
                next_city = i
    memo[curr][mask] = ans
    parent[curr][mask] = next_city
    return ans


def tsp(cost, start):
    global start_node
    start_node = start  

    n = len(cost)
    memo = [[-1] * (1 << n) for _ in range(n)]
    parent = [[-1] * (1 << n) for _ in range(n)]
    min_cost = totalCost(1 << start_node, start_node, n, cost, memo, parent)
    path = []
    mask = 1 << start_node
    curr = start_node
    while curr != -1:
        path.append(curr)
        curr = parent[curr][mask]
        if curr != -1:
            mask |= (1 << curr)
    path.append(start_node)
    return min_cost, path

def cost_matrix(result):
    
    n = len(result)
    return [[((result[j]['center_x'] - result[i]['center_x']) ** 2 +
              (result[j]['center_y'] - result[i]['center_y']) ** 2)
             for j in range(n)] for i in range(n)]
def decode_node(tour, result):
    
    return [(result[i]['center_x'], result[i]['center_y']) for i in tour] + \
           [(result[tour[0]]['center_x'], result[tour[0]]['center_y'])]


def find_starting_node(result_list, start_shape, start_color):
    """Find the index of the starting node based on shape and color."""
    for i, item in enumerate(result_list):
        if item['shape'] == start_shape and item['color'] == start_color:
            return i
    raise ValueError(f"No object found with shape '{start_shape}' and color '{start_color}'.")

def arrange_by_coordinates(result_list, node_cord):

    arranged_list = []
    
    for x, y in node_cord:
        for item in result_list:
            if item['center_x'] == x and item['center_y'] == y:
                arranged_list.append(item)
                break
    # list=send(arranged_list)                
                
    return list
def directions_creation(image, nodes):
                    
    for i in range(len(nodes) - 1):
        cv2.line(image, nodes[i], nodes[i + 1], (128, 0, 128), 2)
        cv2.imshow('Path', image)
        cv2.waitKey(500)
    cv2.waitKey(0)
def shortest_path(image):
    print("inside the function")
    _,result_list=identify_shapes_and_colors(image)
    cost = cost_matrix(result_list)
    # start_node = find_starting_node(result_list, "rectangle", "red")#randomly giving the value of shape and color
    start_node=0
    print("\n\n start_node",start_node)
    min_cost,best_tour = tsp(cost, start_node)
    node_coords = decode_node(best_tour, result_list)
    print("\n\n node_coords",node_coords)
    return node_coords
    # return arrange_by_coordinates(result_list, node_coords)
if __name__ == "__main__":
    start_client()
