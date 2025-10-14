#TO DO:
# Fill roll and pitch gauges based on the variables
# Add text version of the info
# Add Barometer bar
# Add drone visualisation
import pygame
import pygame_gui
import math
import Input

pygame.init()
pygame.joystick.init()
Input.controller_init()
from Input import controller

#Diverse variables
thrust = 00
thrust_level = 100
heading = 0
pitch = 0
roll = 0
voltage = 2
current = 1
prev_voltage = 1
prev_current = 0
height = 10

gauge_text = pygame.font.SysFont("Arial", 16)

text_gui = True
Gui_button_text = "Text GUI"
pygame.display.set_caption("Drone GUI")

window_surface = pygame.display.set_mode((800, 600))


def draw_wedge(surface, center, radius, data, color=(255, 0, 0)):
    start_angle = math.radians(0-90)          # -90 so 0° is at top
    end_angle   = math.radians(data-90)

    # Build the list of points for the wedge
    points = [center]
    steps = max(12, int(abs(data) / 3))  #smoothness
    for i in range(steps + 1):
        angle = start_angle + (end_angle - start_angle) * i / steps
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        points.append((x, y))

    pygame.draw.polygon(surface, color, points)


window = pygame.Surface((800, 600))
window.fill(pygame.Color("#C0C0C0"))
manager = pygame_gui.UIManager((800, 600))

#Flight path



#Gauges init
thrust_text = gauge_text.render("Thrust power", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
thruster_gauge = pygame.image.load('Firmware/Controller/Gui elements/Thrust-gauge.png')

pitch_text = gauge_text.render("Pitch", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
pitch_gauge_back = pygame.image.load('Firmware/Controller/Gui elements/Gauge_template_empty.png')
pitch_gauge = pygame.image.load('Firmware/Controller/Gui elements/Gauge_pitch_text.png')

roll_text = gauge_text.render("Roll", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
roll_gauge_back = pygame.image.load('Firmware/Controller/Gui elements/Gauge_template_empty.png')
roll_gauge = pygame.image.load('Firmware/Controller/Gui elements/Gauge_rol_text.png')

heading_text = gauge_text.render("Heading", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
heading_gauge_back = pygame.image.load('Firmware/Controller/Gui elements/Gauge_template_empty.png')
heading_gauge = pygame.image.load('Firmware/Controller/Gui elements/Gauge_heading_text.png')

battery_text = gauge_text.render("Battery status:", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
battery_voltage = gauge_text.render(f"Voltage: {voltage}V", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
battery_current = gauge_text.render(f"Current: {current}A", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)

#Bottom button creation
hello_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 500), (270, 100)), text='Thruster speed', manager=manager)
Gui_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((265, 500), (273, 100)), text=Gui_button_text, manager=manager)
controll_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((530, 500), (273, 100)), text='Toggle Controller', manager=manager)


#Draw gauges
def draw_gauges():
    #Pitch gauge
    window.blit(pitch_gauge_back, (35,50))
    window.blit(pitch_gauge, (35,50))
    window.blit(pitch_text, (79,30))

    
    #Roll gauge
    window.blit(roll_gauge_back, (35,200))
    window.blit(roll_gauge, (35,200))
    window.blit(roll_text, (80, 180))

    #Heading gauge
    window.blit(heading_gauge_back, (35,350))
    global heading
    if heading >=0:
        draw_wedge(window,(95, 410),59,heading,(255,0,0))
        if heading >= +180:
            heading -=359
    else:
        draw_wedge(window,(95, 410),59,heading,(255,0,0))
        if  heading <= -180:
            heading +=359
    window.blit(heading_gauge, (35,350))
    window.blit(heading_text, (67, 330))

    pygame.draw.rect(window, (255, 0, 0), [700, 320, 40, 20], 0)
    max_height = 335
    bar_bottom_y = 340  # bottom of the gauge
    # calculate the current height of the thrust bar based on thrust value
    current_height = min(thrust, max_height)
    # calculate the top-left y coordinate so it grows upwards
    top_y = bar_bottom_y - current_height
    # draw the rectangle
    pygame.draw.rect(window, (255, 0, 0), [700, top_y-20, 40, current_height], 0)
    window.blit(thruster_gauge, (700,100))
    window.blit(thrust_text, (672, 75))

    #Update battery text
    battery_voltage = gauge_text.render(f"Voltage: {voltage}V", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    battery_current = gauge_text.render(f"Current: {current}A", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    window.blit(battery_text, (670, 430))
    window.blit(battery_voltage, (670, 450))
    window.blit(battery_current, (670, 470))

def draw_text_view():

    pitch_value  = gauge_text.render(f"Pitch: {pitch} deg", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    heading_value  = gauge_text.render(f"Heading: {round(heading,0)} deg", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    roll_value  = gauge_text.render(f"Roll: {roll} deg", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    thrust_value  = gauge_text.render(f"Thrust: {round(thrust/2,0)}%", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    height_value  = gauge_text.render(f"Height: {round(height)}m", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    window.blit(pitch_value,(10,30))
    window.blit(roll_value,(10,50))
    window.blit(heading_value,(10,70))
    window.blit(thrust_value,(10,90))
    window.blit(height_value,(10,110))

    #Update battery text
    battery_voltage = gauge_text.render(f"Voltage: {voltage}V", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    battery_current = gauge_text.render(f"Current: {current}A", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    window.blit(battery_text, (10, 430))
    window.blit(battery_voltage, (10, 450))
    window.blit(battery_current, (10, 470))


clock = pygame.time.Clock()
is_running = True


while is_running:
    time_delta = clock.tick(60)/1000.0

    #Initial fram draw
    pygame.draw.rect(window,"#C0C0C0", [0, 0, 800, 600],0)
    if (text_gui):
        draw_text_view()
    else:
        draw_gauges()

    #Continous controller handler
    if controller.get_button(9): #Bumper L pushed
                heading -= 20 * time_delta
    if controller.get_button(10): #Bumper R pushed
                heading += 20 * time_delta

    #Event handler
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False
        
        #Keypress events
        if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    pitch += 1
                    print(f"Pitching forward!\nPitch is now {pitch}")
                elif event.key == pygame.K_s:
                    pitch -= 1
                    print(f"Pitching backward!\nPitch is now {pitch}")
                elif event.key == pygame.K_d:
                    roll += 1
                    print(f"Rolling left!\nRoll is now {roll}")
                elif event.key == pygame.K_a:
                    roll -= 1
                    print(f"Rolling right!\nRoll is now {roll}")
                elif event.key == pygame.K_e:
                    heading +=10
                    print(f"Turning right!\nHeading is now {heading}")
                elif event.key == pygame.K_q:
                    heading -=10
                    print(f"Turning left!\nHeading is now {heading}")
                elif (event.key == pygame.K_UP and thrust_level < 200):
                    thrust_level += 1
                    print(f"Thrust up!\nThrust is now {thrust}")
                elif (event.key == pygame.K_DOWN and thrust_level > 0):
                    thrust_level -= 1
                    print(f"Thrust down!\nThrust is now {thrust}")
        
        #UI events
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == hello_button:
                thrust = thrust + 10
            if event.ui_element == Gui_button:
                text_gui = not text_gui
                if (text_gui):
                    Gui_button.set_text("Visual GUI")
                else:
                    Gui_button.set_text("Text GUI")
                print(f"Gui switch is pressed and text state is {text_gui}")
            if event.ui_element == controll_button:
                print('Controller enabled')


        #Controller events
        if event.type == pygame.JOYBUTTONDOWN:
            #Switch pro controller buttons
            if controller.get_button(0): #Button A pushed
                print("Button A pushed")
            if controller.get_button(1): #Button B pushed
                print("Button B pushed")
            if controller.get_button(2): #Button X pushed
                print("Button X pushed")
            if controller.get_button(3): #Button Y pushed
                print("Button Y pushed") 
            if controller.get_button(4): #Button - pushed
                print("Button - pushed")
            if controller.get_button(5): #Button Home pushed
                print("Button Home pushed")
            if controller.get_button(6): #Button + pushed
                print("Button + pushed")
            if controller.get_button(7): #Button L3 pushed
                print("Button L3 pushed")
            if controller.get_button(8): #Button R3 pushed
                print("Button R3 pushed")
            if controller.get_button(11):#Dpad up pushed
                thrust_level += 10
            if controller.get_button(12):#Dpad down pushed
                thrust_level -= 10
            if controller.get_button(13):#Dpad Left pushed
                heading -= 5
            if controller.get_button(14):#Dpad Right pushed
                heading += 5
            if controller.get_button(15):#Button screnshot pushed
                text_gui = not text_gui

        #Joystick event
        if event.type == pygame.JOYAXISMOTION:
            left_x_axis = controller.get_axis(0)
            Left_y_axis = controller.get_axis(1)*-1
            right_x_axis = controller.get_axis(2)
            thrust = ((controller.get_axis(3)*-1)+1)* thrust_level #Left stick up and down




        manager.process_events(event)


    manager.update(time_delta)
    window_surface.blit(window, (0, 0))
    manager.draw_ui(window_surface)
    pygame.display.update()