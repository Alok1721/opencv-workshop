import cv2
import numpy as np
from itertools import permutations


def calculate_tour_distance(adj_matrix, tour):
    total_distance = 0
    for i in range(len(tour) - 1):
        total_distance += adj_matrix[tour[i]][tour[i + 1]]
    total_distance += adj_matrix[tour[-1]][tour[0]]  # Return to the start
    return total_distance


def find_best_tour(adj_matrix, start_node):  
    num_cities = len(adj_matrix)
    cities = [i for i in range(num_cities) if i != start_node]
    best_tour = []
    min_cost = float('inf')

    for perm in permutations(cities):
        tour = [start_node] + list(perm)
        cost = calculate_tour_distance(adj_matrix, tour)
        if cost < min_cost:
            min_cost = cost
            best_tour = tour

    return best_tour



def detect_shapes_and_colors(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    color_ranges = {
        'red': [
            (np.array([0, 100, 100]), np.array([10, 255, 255])),
            (np.array([160, 100, 100]), np.array([180, 255, 255]))
        ],
        'blue': [(np.array([90, 50, 50]), np.array([130, 255, 255]))],
        'green': [(np.array([40, 100, 100]), np.array([80, 255, 255]))],
    }
    result_list = []

    for color_name, ranges in color_ranges.items():
        color_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
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
                shape = "square" if 0.95 <= aspect_ratio <= 1.05 else "rectangle"
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

    return result_list

def send(shape_list):
    
    result_list = []
    
    for item in shape_list:
        
        simplified_item = {
            'shape': item['shape'],
            'color': item['color']
        }
        result_list.append(simplified_item)
    
    return result_list

def cost_matrix(result):
    
    n = len(result)
    return [[((result[j]['center_x'] - result[i]['center_x']) ** 2 +
              (result[j]['center_y'] - result[i]['center_y']) ** 2)
             for j in range(n)] for i in range(n)]


def decode_node(tour, result):
    
    return [(result[i]['center_x'], result[i]['center_y']) for i in tour] + \
           [(result[tour[0]]['center_x'], result[tour[0]]['center_y'])]


def directions_creation(image, nodes):
                    
    for i in range(len(nodes) - 1):
        cv2.line(image, nodes[i], nodes[i + 1], (128, 0, 128), 2)
        cv2.imshow('Path', image)
        cv2.waitKey(500)
    cv2.waitKey(0)


def find_starting_node(result_list, start_shape, start_color):
    """Find the index of the starting node based on shape and color."""
    for i, item in enumerate(result_list):
        if item['shape'] == start_shape and item['color'] == start_color:
            return i
    raise ValueError(f"No object found with shape '{start_shape}' and color '{start_color}'.")


def path(image_path, start_shape, start_color):
    
    image = cv2.imread(image_path)
    result_list = detect_shapes_and_colors(image)

    if not result_list:
        print("No objects detected.")
        return

    for item in result_list:
        cv2.circle(image, (item['center_x'], item['center_y']), 3, (255, 255, 255), -1)
        text = f"{item['color']} {item['shape']}"
        cv2.putText(image, text, (item['center_x'] - 40, item['center_y'] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    cost = cost_matrix(result_list)
    start_node = find_starting_node(result_list, start_shape, start_color)
    best_tour = find_best_tour(cost, start_node)
    node_coords = decode_node(best_tour, result_list)
    
    print("hi")
    

    directions_creation(image, node_coords)
def arrange_by_coordinates(result_list, node_cord):

    arranged_list = []
    
    for x, y in node_cord:
        for item in result_list:
            if item['center_x'] == x and item['center_y'] == y:
                arranged_list.append(item)
                break
    list=send(arranged_list)                
                
    return list

def shortest_path(image):
    result_list=detect_shapes_and_colors(image)
    cost = cost_matrix(result_list)
    start_node = find_starting_node(result_list, start_shape, start_color)
    best_tour = find_best_tour(cost, start_node)
    node_coords = decode_node(best_tour, result_list)
    return arrange_by_coordinates(result_list, node_coords)

image_path = "test.png"#hid.png
start_shape = "triangle"
start_color = "blue"
image = cv2.imread(image_path)
# path(image_path, start_shape, start_color)

# print(shortest_path(image))
path(image_path,start_shape,start_color)