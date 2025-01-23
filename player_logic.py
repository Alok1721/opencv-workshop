import cv2
import numpy as np



def identify_shapes_and_colors(frame):
    """Identify shapes and colors using simplified HSV mapping."""
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

            result_list.append((shape, color_name))
            cv2.putText(frame, str(shape), (center_x, center_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.drawContours(frame, [approx], 0, (255, 255, 255), -1)
            x, y, w, h = cv2.boundingRect(approx)
         

    return frame, result_list