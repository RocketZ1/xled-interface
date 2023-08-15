import time
import tkinter as tk

import HandTracking_Calibration
import cv2
import mediapipe as mp
from PIL import Image, ImageTk
from xled_plus.effect_base import Effect
from xled_plus.highcontrol import HighControlInterface
from xled_plus.ledcolor import image_to_led_rgb


class PictureEffect(Effect):
    def __init__(self, ctr, frame, fit='stretch'):
        # fit can be: 'stretch', 'small', 'large', 'medium'
        super(PictureEffect, self).__init__(ctr)
        self.im = frame
        self.xmid = (self.im.size[0] - 1) / 2.0
        self.ymid = (self.im.size[1] - 1) / 2.0
        if fit == 'stretch':
            self.xscale = self.im.size[0] - 1
            self.yscale = self.im.size[1] - 1
        else:
            bounds = ctr.get_layout_bounds()
            xdiff = bounds["bounds"][0][1] - bounds["bounds"][0][0]
            if xdiff == 0.0:
                xdiff = 1.0
            if fit == 'small':
                fact = max((self.im.size[0] - 1) / xdiff, self.im.size[1] - 1)
            elif fit == 'large':
                fact = min((self.im.size[0] - 1) / xdiff, self.im.size[1] - 1)
            else:
                fact = ((self.im.size[0] - 1) * (self.im.size[0] - 1) / xdiff) ** 0.5
            self.xscale = xdiff * fact
            self.yscale = fact
        # print('test123')
        if "is_animated" in dir(self.im) and self.im.is_animated:
            self.preferred_fps = 100.0 / self.im.info["duration"]
            self.preferred_frames = self.im.n_frames
        else:
            self.preferred_fps = 1
            self.preferred_frames = 1

    def get_color(self, pos):
        coord = (int(round((pos[0] - 0.5) * self.xscale + self.xmid)),
                 int(round((0.5 - pos[1]) * self.yscale + self.ymid)))
        if 0 <= coord[0] < self.im.size[0] and 0 <= coord[1] < self.im.size[1]:
            if self.im.mode == 'P':
                pix = self.im.getpixel(coord)
                rgb = self.im.getpalette()[pix * 3:pix * 3 + 3]
            elif self.im.mode == 'L':
                rgb = [self.im.getpixel(coord)] * 3
            else:
                rgb = self.im.getpixel(coord)[0:3]
        else:
            rgb = (0, 0, 0)
        return image_to_led_rgb(*rgb)

    def reset(self, numframes):
        self.index = -1

    def getnext(self):
        if "is_animated" in dir(self.im) and self.im.is_animated:
            self.index += 1
            self.im.seek(self.index % self.im.n_frames)
        return self.ctr.make_layout_pattern(self.get_color, style="square")


def send_image(left_frame, right_frame):
    p1 = PictureEffect(ctr1, right_frame)
    p2 = PictureEffect(ctr2, left_frame)
    p1.launch_rt()
    p2.launch_rt()


def show_pc_frame(current_frame):
    label.img = current_frame
    label.config(image=current_frame)
    root.update()


root = tk.Tk()
root.title("Webcam Stream")
label = tk.Label(root)
label.pack()


def capture_webcam_image(cam, displayImage):
    if not cam.isOpened():
        print("Error: Webcam not available or not found.")
        return

    # Read a frame from the webcam
    ret, current_frame = cam.read()

    if not ret:
        return None

    current_frame = current_frame[:, :, [2, 1, 0]]  # Swap R and B channels

    if displayImage:
        img = Image.fromarray(current_frame)
        img = ImageTk.PhotoImage(image=img)
        show_pc_frame(img)

    rotated_frame = cv2.transpose(current_frame)
    rotated_frame = cv2.flip(rotated_frame, 1)
    # Swap Red and blue channels because they are swapped by default?

    return rotated_frame


def rotate_image(image):
    # Rotate the image by 90 degrees to the right
    rotated_image = image.rotate(-90, expand=True)
    return rotated_image


def split_image_vertically(PIL_Image):
    image = PIL_Image

    # Get the size of the image (width and height)
    width, height = image.size

    # Calculate the mid-point for vertical splitting
    mid = width // 2

    # Crop the image into two parts
    left_part = image.crop((0, 0, mid, height))
    right_part = image.crop((mid, 0, width, height))
    return left_part, right_part


# Debug tool to calibrate LEDS
def handDrawImage():
    width, height = 32, 24
    background_color = (255, 255, 255)  # RGB white color
    img = Image.new("RGB", (width, height), background_color)
    for x in range(32):
        for y in range(24):
            red = 256
            green = 0
            blue = 0
            img.putpixel((x, y), (red, green, blue))
            left_part, right_part = split_image_vertically(img)
            send_image(left_part, right_part)
            HandTracking_Calibration.nextPixel(x, y)
            time.sleep(0.15)
            img.putpixel((x, y), (256, 256, 256))
            time.sleep(0.15)
    img.putpixel((31, 23), (256, 256, 256))
    HandTracking_Calibration.closeScanner()


def loadLEDBounds():
    file = open('LED_Bounds.txt', 'r')
    ledBounds = []
    for led in file:
        ledBoundData = led.split(',')
        ledBoundData[3].replace('\n', '')
        ledBounds.append(ledBoundData)
    return ledBounds


def checkIntercept(x, y, bounding_boxes):
    for i, box in enumerate(bounding_boxes):
        x1, y1, x2, y2 = map(int, box)
        if x1 <= x <= x2 and y1 <= y <= y2:
            return i  # Return the index of the intercepted bounding box
    return -1  # No interception found


def fingerPaint():
    LED_Bounds = loadLEDBounds()
    # Initialize Mediapipe hands module
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands()

    # Open the webcam
    cam = cv2.VideoCapture(0)
    width, height = 32, 24
    background_color = (255, 255, 255)  # RGB white color
    img = Image.new("RGB", (width, height), background_color)

    while True:
        ret, frame = cam.read()

        if not ret:
            break

        # Convert BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame using Mediapipe hands module
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Get the x, y coordinates of the tip of the pointer finger (index 8)
                tip_x = int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x * frame.shape[1])
                tip_y = int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y * frame.shape[0])

                # Draw a circle at the tip of the pointer finger
                cv2.circle(frame, (tip_x, tip_y), 5, (0, 0, 255), -1)

                # Print the x, y coordinates
                # print(f"Tip of pointer finger - X: {tip_x}, Y: {tip_y}")
                led_index = checkIntercept(tip_x, tip_y, LED_Bounds)
                if led_index == -1:
                    continue
                print(led_index, tip_x, tip_y)
                red = 0
                green = 256
                blue = 0
                x = led_index // height
                y = led_index % height
                print(x, y)
                img.putpixel((x, y), (red, green, blue))
                left_part, right_part = split_image_vertically(img)
                send_image(left_part, right_part)

        # Display the frame with annotations
        cv2.imshow("Finger Tracking", frame)
        #
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


def loadVideoFile(vid_path, rotateVideo=False):
    vid = cv2.VideoCapture(vid_path)
    # Check if the video file was opened successfully
    if not vid.isOpened():
        print("Error opening video file.")
        return

    print("Opened Video")
    while True:
        # Read a frame from the video
        ret, frame = vid.read()
        # Break the loop if no more frames are available
        if not ret:
            break

        # Convert the frame to RGB format
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convert the frame to a PIL Image
        pil_image = Image.fromarray(frame_rgb)

        if rotateVideo:
            pil_image = rotate_image(pil_image)

        # Display the frame
        left_part, right_part = split_image_vertically(pil_image)
        time.sleep(0.04)
        send_image(left_part, right_part)

    print("Video Complete")
    vid.release()
    cv2.destroyAllWindows()


# Light Board 1 & 2
host1 = '192.168.254.196'
host2 = '192.168.254.197'

ctr1 = HighControlInterface(host1)
ctr2 = HighControlInterface(host2)

if __name__ == '__main__':
    # Re-calibrate finger painting
    reset_LED_bounds = False

    if reset_LED_bounds:
        handDrawImage()

    # COMMANDS
    useWebCam = False
    handDrawing = False
    displayFileImage = False
    displayVideoFile = True

    # The cool one
    fingerPainting = False

    file = "image_path.jpg"

    if fingerPainting:
        fingerPaint()

    elif useWebCam:
        # Create a VideoCapture object to access the webcam (0 is the default webcam index)
        cap = cv2.VideoCapture(0)

        while True:
            currentFrame = capture_webcam_image(cap, True)
            if currentFrame is None:
                print("Failed to capture webcam frame!")
                continue

            image = Image.fromarray(currentFrame)
            left_part, right_part = split_image_vertically(image)
            startTime = time.time()
            send_image(left_part, right_part)
            timeElapsed = time.time() - startTime
            print(timeElapsed)
    elif handDrawing:
        handDrawImage()
    elif displayFileImage:
        image = Image.open(file)
        left_part, right_part = split_image_vertically(image)
        startTime = time.time()
        send_image(left_part, right_part)
        timeElapsed = time.time() - startTime
        print(timeElapsed)
    elif displayVideoFile:
        video_path = "video_path.mp4"
        loadVideoFile(video_path, True)
