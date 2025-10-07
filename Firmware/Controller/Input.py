import pygame
import time

pygame.init()
pygame.joystick.init()
def controller_init():
    # List the available joystick devices
    global controller
    controller = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]

    # Initialize all detected joysticks
    for controller in controller:
        print(f"Joystick {controller.get_instance_id()}: {controller.get_name()}")

times = 0
# Example: Print the position of the left and right analog sticks for all detected joysticks
"""
while True:
    pygame.event.get()
    if event.type == joystick.
    #Switch pro controller buttons
    if joystick.get_button(0):
        print("Button A pushed")
    if joystick.get_button(1):
        print("Button B pushed")
    if joystick.get_button(2):
        print("Button X pushed")
    if joystick.get_button(3):
        print("Button Y pushed")
    if joystick.get_button(4):
        print("Button - pushed")
    if joystick.get_button(5):
        print("Button Home pushed")
    if joystick.get_button(6):
        print("Button + pushed")
    if joystick.get_button(7):
        print("Button L3 pushed")
    if joystick.get_button(8):
        print("Button R3 pushed")
    if joystick.get_button(9):
        print("Bumper L pushed")
    if joystick.get_button(10):
        print("Bumper R pushed")
    if joystick.get_button(11):
        print("Dpad up pushed")
    if joystick.get_button(12):
        print("Dpad down pushed")
    if joystick.get_button(13):
        print("Dpad Left pushed")
    if joystick.get_button(14):
        print("Dpad right pushed")
    if joystick.get_button(15):
        print("Button Screenshot pushed")
"""

    #for joystick in joysticks:
     #   left_x_axis = joystick.get_axis(0)
      #  left_y_axis = joystick.get_axis(1)
       # right_x_axis = joystick.get_axis(2)
        #right_y_axis = joystick.get_axis(3)
        #print(f"Left Joystick: X={left_x_axis}, Y={left_y_axis}, Right Joystick: X={right_x_axis}, Y={right_y_axis}")
        #time.sleep(1)