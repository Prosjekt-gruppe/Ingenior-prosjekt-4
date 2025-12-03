#TO DO:
# Fill roll and pitch gauges based on the variables
# Add Barometer bar
# Add drone visualisation

import pygame
import pygame_gui
import math
import Input
import serial
import threading
import time
import json
from serial.tools import list_ports

pygame.init()
pygame.joystick.init()

#Diverse variables
thrust = 00
thrust_level = 100
heading = 0
pitch = 0
roll = 0
voltage = 2#V
current = 1#A
prev_voltage = 1#V
prev_current = 0#A
altitude = 10 #m

text_gui = False
settings_gui = False
baudrate = 9600
com_port = "dev/ttyUSB0"
gauge_text = pygame.font.SysFont("Arial", 16)

Gui_button_text = "Text GUI"
com_buttons = []
selected_port = None
baudrate_options = ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]

pygame.display.set_caption("Drone GUI")

window_surface = pygame.display.set_mode((800, 600))


#Drone communication
def send_data(ser):
        msg = "Controller data.\n"
        ser.write(msg.encode('utf-8'))
        print(f"Data sendt")
        

def receive_data(ser):
    while True:
        if ser.in_waiting > 0:
            received_data = ser.readline().decode().strip()
            print(f"Received: {received_data}")

def create_com_buttons():
    global com_buttons
    for b in com_buttons:
        b.kill()
    com_buttons = []

    ports = list_ports.comports()

    y = 100
    for p in ports:
        # Filter: ignore ports without a meaningful description
        if p.description and p.description.lower() != "n/a":
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((310, y), (300, 30)),
                text=f"{p.device}  -  {p.description}",
                manager=manager
            )
            com_buttons.append(btn)
            y += 40

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


def draw_center_out_fill(surface, center, radius, value, max_value=90, color=(128,0,0)):
    # Clamp the value
    value = max(-max_value, min(max_value, value))

    # Determine fill width proportionally
    fill_ratio = abs(value) / max_value
    fill_width = radius * fill_ratio

    # Create a rect for the fill
    if value > 0:
        fill_rect = pygame.Rect(center[0], center[1]-radius, fill_width, radius*2)
    else:
        fill_rect = pygame.Rect(center[0]-fill_width, center[1]-radius, fill_width, radius*2)

    # Draw the fill
    pygame.draw.rect(surface, color, fill_rect)







window = pygame.Surface((800, 600))
window.fill(pygame.Color("#C0C0C0"))
manager = pygame_gui.UIManager((800, 600))

#Gauges init
thrust_text = gauge_text.render("Thrust power", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
thruster_gauge = pygame.image.load('Firmware/Controller/Gui elements/Thrust-gauge.png')

pitch_text = gauge_text.render("Pitch", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
pitch_gauge_back = pygame.image.load('Firmware/Controller/Gui elements/Gauge_template_empty.png')
pitch_gauge = pygame.image.load('Firmware/Controller/Gui elements/Gauge_pitch_text.png')

roll_text = gauge_text.render("Roll", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
roll_gauge_back = pygame.image.load('Firmware/Controller/Gui elements/Gauge_template_empty.png')
roll_gauge = pygame.image.load('Firmware/Controller/Gui elements/Gauge_roll_text.png')

heading_text = gauge_text.render("Heading", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
heading_gauge_back = pygame.image.load('Firmware/Controller/Gui elements/Gauge_template_empty.png')
heading_gauge = pygame.image.load('Firmware/Controller/Gui elements/Gauge_heading_text.png')

battery_text = gauge_text.render("Battery status:", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
battery_voltage = gauge_text.render(f"Voltage: {voltage}V", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
battery_current = gauge_text.render(f"Current: {current}A", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)

altitude_text = gauge_text.render("Altitude", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)

background = pygame.image.load("Firmware/Controller/Gui elements/Background.png")
#Bottom button creation
Settings_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 500), (270, 100)), text='Settings', manager=manager)
Gui_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((265, 500), (273, 100)), text=Gui_button_text, manager=manager)
controll_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((530, 500), (273, 100)), text='Toggle Controller', manager=manager)
baudrate_dropdown = pygame_gui.elements.UIDropDownMenu(
    options_list=baudrate_options,
    starting_option=str(baudrate),
    relative_rect=pygame.Rect((390, 30), (120, 25)),
    manager=manager
)


#Draw gauges
def draw_gauges():
    pygame.display.set_caption("Normal view")
    window.blit(background,(0,0))
    #Pitch gauge
    window.blit(pitch_gauge_back, (35,50))
    window.blit(pitch_gauge, (35,50))
    window.blit(pitch_text, (79,30))

    #Roll gauge
    window.blit(roll_gauge_back, (35,200))
    window.blit(roll_gauge, (35,200))
    window.blit(roll_text, (80, 180))
    draw_center_out_fill(window, center=(95, 260), radius=59, value=roll, max_value=90, color=(255,0,0))     

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

    #Thruster level gauge drawing
    max_height = 335
    bar_bottom_y = 415  # bottom of the gauge
    # calculate the current height of the thrust bar based on thrust value
    current_height = min(thrust, max_height)
    # calculate the top-left y coordinate so it grows upwards
    top_y = bar_bottom_y - current_height
    # draw the rectangle
    pygame.draw.rect(window, (255, 0, 0), [700, top_y-20, 40, current_height], 0)
    window.blit(thruster_gauge, (700,175))
    window.blit(thrust_text, (680, 160))

    #Update battery text
    battery_voltage = gauge_text.render(f"Voltage: {voltage}V", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    battery_current = gauge_text.render(f"Current: {current}A", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    window.blit(battery_text, (670, 430))
    window.blit(battery_voltage, (670, 450))
    window.blit(battery_current, (670, 470))


def draw_text_view():
    pygame.display.set_caption("Text view")
    window.blit(background,(0,0))
    pitch_value  = gauge_text.render(f"Pitch: {pitch} deg", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    heading_value  = gauge_text.render(f"Heading: {round(heading,0)} deg", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    roll_value  = gauge_text.render(f"Roll: {roll} deg", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    thrust_value  = gauge_text.render(f"Thrust: {round(thrust/2,0)}%", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    height_value  = gauge_text.render(f"Height: {round(altitude)}m", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
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


def draw_settings_view():
    pygame.display.set_caption("Settings")
    window.blit(background,(0,0))
    baud_text  = gauge_text.render(f"Baudrate: ", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    Com_port_text  = gauge_text.render(f"COM Port:", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    Com_port_current  = gauge_text.render(f"{com_port}", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    pygame.draw.rect(window,"#A1A1A1", (390, 60, 90, 25), 0)
    window.blit(baud_text, (310, 30))
    window.blit(Com_port_text, (310, 60))
    window.blit(Com_port_current, (390, 60))

def draw_barometer(surface,min_altitude, max_altitude ,x, y, width, height, font):
    global altitude
    # Background
    #pygame.draw.rect(surface, "#9e9e9e" , (x, y, width, height))
    pygame.draw.rect(surface, (0, 0, 0), (x, y, width, height), 2)

    # Scale setup
    total_range = max_altitude - min_altitude
    pixels_per_meter = height / total_range

    # Tick spacing
    if total_range > 500:
        tick_step = 100
    elif total_range > 200:
        tick_step = 50
    elif total_range > 50:
        tick_step = 10
    elif total_range > 20:
        tick_step = 5
    else:
        tick_step = 1

    # Draw tick marks and labels
    for alt in range(0, int(max_altitude) + 1, tick_step):
        y_pos = y + height - (alt - min_altitude) * pixels_per_meter
        if y <= y_pos <= y + height:
            #Gauge notches
            pygame.draw.line(surface, (0, 0, 0), (x, y_pos), (x + 15, y_pos), 1)
            pygame.draw.line(surface, (0, 0, 0), (x + width - 15, y_pos), (x + width, y_pos), 1)
            # Label on the left/outside
            label = font.render(f"{alt}", True, (0, 0, 0))
            label_rect = label.get_rect(midright=(x - 5, y_pos))
            surface.blit(label, label_rect)

    # --- Compute the marker position ---
    zero_y = y + height - (0 - min_altitude) * pixels_per_meter
    if altitude < 0:
        red_y = zero_y
    else:
        red_y = y + height - (altitude - min_altitude) * pixels_per_meter
        red_y = max(y, min(red_y, y + height))

    # Draw red indicator
    pygame.draw.rect(surface, (255, 0, 0), (x, red_y - 1, width, 2))

    # Numeric readout (shows true altitude, can also be placed outside)
    text = font.render(f"{altitude:.1f} m", True, (0, 0, 0))
    text_rect = text.get_rect(midleft=(x + width - 60, red_y-5))
    surface.blit(text, text_rect)
    surface.blit(altitude_text,(x+10,y-40))



# bound rate on two ports must be the same
#Chane to runtime check
#ser = serial.Serial('/dev/ttyUSB0', 115200)
#print(ser.portstr)
#time.sleep(0.5)
#tx = threading.Thread(target=send_data, args=(ser,))
#rx = threading.Thread(target=receive_data, args=(ser,), daemon=True)
#tx.start()
#rx.start()



clock = pygame.time.Clock()
is_running = True
while is_running:
    time_delta = clock.tick(60)/1000.0
    Input.Is_controller_attatched() #Checks for a connected controller every loop

    if(text_gui):
        Gui_button.set_text("Visual GUI")
        Settings_button.set_text("Settings")
    elif(settings_gui):
        Settings_button.set_text("Visual GUI")
        Gui_button.set_text("Text Gui")
        create_com_buttons()
    else:
        Settings_button.set_text("Settings")
        Gui_button.set_text("Text Gui")

    if(thrust > 200):
        thrust = 200
    elif (thrust < 0):
        thrust = 0

    #Initial fram draw
    pygame.draw.rect(window,"#C0C0C0", [0, 0, 800, 600],0)#clear screen for clean redraw
    if (text_gui):
        draw_text_view()
        baudrate_dropdown.hide()
    elif(settings_gui):
        draw_settings_view()
        baudrate_dropdown.show()
    else:
        draw_gauges()
        draw_barometer(window,-10, 300, 600, 200, 75, 200, gauge_text)
        baudrate_dropdown.hide()
        
    #Continous controller handler
    if(Input.controller != None):
        if Input.controller.get_button(9): #Bumper L pushed
                    heading -= 20 * time_delta
        if Input.controller.get_button(10): #Bumper R pushed
                    heading += 20 * time_delta

    #Event handler
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False
        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == baudrate_dropdown:
                baudrate = int(event.text)
                print("Baudrate changed to:", baudrate)

        
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
                elif event.key == pygame.K_KP8:
                    altitude += 0.5
                    print(f"altitude up")
                elif event.key == pygame.K_KP2:
                    altitude -= 0.5
                    print(f"altitude down")
        
        #UI events
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == Settings_button:
                settings_gui = not settings_gui
                text_gui = False
                Settings_button.set_text("Visual GUI")
            if event.ui_element == Gui_button:
                text_gui = not text_gui
                settings_gui = False
                print(f"Gui switch is pressed and text state is {text_gui}")
            if event.ui_element == controll_button:
                print('Controller enabled')


        #Controller events
        if((event.type == pygame.JOYBUTTONDOWN) and (Input.controller != None)):
            #Switch pro controller buttons
            if Input.controller.get_button(0): #Button A pushed
                print("Button A pushed")
            if Input.controller.get_button(1): #Button B pushed
                print("Button B pushed")
            if Input.controller.get_button(2): #Button X pushed
                print("Button X pushed")
            if Input.controller.get_button(3): #Button Y pushed
                print("Button Y pushed") 
            if Input.controller.get_button(4): #Button - pushed
                print("Button - pushed")
            if Input.controller.get_button(5): #Button Home pushed
                print("Button Home pushed")
            if Input.controller.get_button(6): #Button + pushed
                print("Button + pushed")
            if Input.controller.get_button(7): #Button L3 pushed
                print("Button L3 pushed")
            if Input.controller.get_button(8): #Button R3 pushed
                print("Button R3 pushed")
            if Input.controller.get_button(11):#Dpad up pushed
                thrust_level += 10
            if Input.controller.get_button(12):#Dpad down pushed
                thrust_level -= 10
            if Input.controller.get_button(13):#Dpad Left pushed
                heading -= 5
            if Input.controller.get_button(14):#Dpad Right pushed
                heading += 5
            if Input.controller.get_button(15):#Button screnshot pushed
                text_gui = not text_gui

        #Joystick event
        if((event.type == pygame.JOYAXISMOTION) and (Input.controller != None)):
            left_x_axis = Input.controller.get_axis(0)
            Left_y_axis = Input.controller.get_axis(1)*-1
            right_x_axis = Input.controller.get_axis(2)
            thrust = ((Input.controller.get_axis(3)*-1)+1)* thrust_level #Left stick up and down



        manager.process_events(event)

    manager.update(time_delta)
    window_surface.blit(window, (0, 0))
    manager.draw_ui(window_surface)
    pygame.display.update()