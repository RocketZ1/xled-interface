import random, keyboard
import threading
import time

import BoardController
from PIL import Image

background_color = (0, 0, 0)  # RGB black color


def startup():
    img = Image.new("RGB", (board_width, board_height), background_color)
    return img


gameOver = False


def endGame():
    print("Game Over!")
    global gameOver
    gameOver = True


last_inputted_vector = 90
new_player_vector = 90


def gattherPlayerInput():
    global new_player_vector
    global last_inputted_vector
    while True:
        if gameOver:
            break
        time.sleep(0.05)
        if keyboard.is_pressed("left") and last_inputted_vector != 180:
            new_player_vector = 0
        elif keyboard.is_pressed("up") and last_inputted_vector != 270:
            new_player_vector = 90
        elif keyboard.is_pressed("right") and last_inputted_vector != 0:
            new_player_vector = 180
        elif keyboard.is_pressed("down") and last_inputted_vector != 90:
            new_player_vector = 270


def getPlayerVector():
    global last_inputted_vector
    global new_player_vector
    # Delay between movements
    # time_delay = (1 / len(snake_body))
    # if time_delay < 0.3:
    #     time_delay = 0.3
    time_delay = 0.3
    time.sleep(time_delay)
    # Pass player vector
    last_inputted_vector = new_player_vector
    return last_inputted_vector

    # vector = int(input("Enter a vector (0, 90, 180, 270)"))
    # return vector


def moveSnake(vector):
    global snake_body
    new_body = []
    for i in range(1, len(snake_body)):
        if i == len(snake_body) - 1:
            # Save pos to turn to disable LED later
            global deleted_tail_pos
            deleted_tail_pos = (snake_body[i][0], snake_body[i][1])
        new_body.append(snake_body[i - 1])

    x, y = new_body[0]
    if vector == 0:
        x += 1
    elif vector == 90:
        y += 1
    elif vector == 180:
        x -= 1
    elif vector == 270:
        y -= 1
    new_body.insert(0, [x, y])
    snake_body = new_body


applePos = []


def spawnApple():
    global applePos
    while True:
        rand_x = random.randrange(1, 32)
        rand_y = random.randrange(1, 24)
        new_apple_pos = [rand_x, rand_y]
        if validMove(new_apple_pos):
            applePos = new_apple_pos
            break


def validMove(new_pos):
    new_x, new_y = new_pos
    if new_x > board_width or new_x < 1 or new_y > board_height or new_y < 1:
        return False

    for body in range(1, len(snake_body)):
        body_x, body_y = snake_body[body]
        if body_x == new_x and body_y == new_y:
            return False
    return True


deleted_tail_pos = ()


def updateBoard():
    # x = led_index // board_height
    # y = led_index % board_height
    red = 0
    green = 256
    blue = 0
    # Remove tail
    board_img.putpixel((deleted_tail_pos[0] - 1, deleted_tail_pos[1] - 1), background_color)
    # Set snake body
    for body in snake_body:
        x, y = body
        board_img.putpixel((x - 1, y - 1), (red, green, blue))

    # Set snake head
    head_color = (255, 255, 0)
    head_pos = (snake_body[0][0] - 1, snake_body[0][1] - 1)
    board_img.putpixel(head_pos, head_color)

    # Set apple
    apple_color = (256, 0, 0)
    apple_pos = (applePos[0] - 1, applePos[1] - 1)
    board_img.putpixel(apple_pos, apple_color)

    # Send image to board
    img1, img2 = BoardController.split_image_vertically(board_img)
    BoardController.send_image(img1, img2)


board_width, board_height = 32, 24
snake_body = [[5, 3], [6, 3], [7, 3], [7, 4]]
board_img = startup()


def loop():
    spawnApple()
    print("test")
    print("start")
    while True:
        vector = getPlayerVector()
        moveSnake(vector)
        valid_move = validMove(snake_body[0])
        if not valid_move:
            endGame()
            break
        head_x, head_y = snake_body[0]
        if head_x == applePos[0] and head_y == applePos[1]:
            snake_body.append([deleted_tail_pos[0], deleted_tail_pos[1]])
            spawnApple()
        updateBoard()


if __name__ == '__main__':
    threading.Thread(target=loop).start()
    print("Started")
    threading.Thread(target=gattherPlayerInput).start()
