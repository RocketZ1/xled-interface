import cv2
import numpy as np


def find_red_led(current_frame):
    # Convert the frame to the HSV color space
    hsv = cv2.cvtColor(current_frame, cv2.COLOR_BGR2HSV)

    # Define the lower and upper bounds of the red color in HSV
    lower_red = np.array([0, 200, 200])
    upper_red = np.array([10, 255, 255])

    # Create a mask to filter the red color
    mask = cv2.inRange(hsv, lower_red, upper_red)

    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    red_led_bounds = []

    for contour in contours:
        # Get the bounding rectangle for each contour
        x, y, w, h = cv2.boundingRect(contour)
        red_led_bounds.append((x, y, x + w, y + h))  # Store the bounding coordinates

    return red_led_bounds


# file = open('LED_Bounds.txt', 'w')


def addBoundsToFile(bounds):
    for x1, y1, x2, y2 in bounds:
        writeString = str(x1) + "," + str(y1) + "," + str(x2) + "," + str(y2) + "\n"
        # file.write(writeString)
        break


cap = cv2.VideoCapture(0)


def nextPixel(x, y):
    ret, frame = cap.read()

    if not ret:
        return False

    red_led_bounds = find_red_led(frame)
    addBoundsToFile(red_led_bounds)
    for x1, y1, x2, y2 in red_led_bounds:
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Draw red bounding rectangle

        # Print the bounds of the red LED
        # print(f"LED ({x},{y}) Bounds: ({x1}, {y1}) - ({x2}, {y2})")
        # Copy and paste this output into LED_Bounds.txt
        print(f"{x1},{y1},{x2},{y2}")
        break

    # Display the frame within the window
    # cv2.imshow("Red LED Detection", frame)
    return True


def closeScanner():
    # file.close()
    cap.release()
    cv2.destroyAllWindows()


