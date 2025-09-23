import pygame
import pygame_gui
import math
import os

pygame.init()

thrust = 00
heading = 0
pitch = 0
roll = 0

gauge_text = pygame.font.SysFont("Arial", 16)

pygame.display.set_caption("Drone GUI")

window_surface = pygame.display.set_mode((800, 600))


def draw_wedge(surface, center, radius, data, color=(255, 0, 0)):
    """
    Draw a filled wedge from 0° up to heading_deg.
    center: (x, y)
    radius: pixels
    heading_deg: angle in degrees, where 0 is straight up
    """
    start_angle = math.radians(0-90)          # -90 so 0° is at top
    end_angle   = math.radians(data-90)

    # Build the list of points for the wedge
    points = [center]
    steps = max(12, int(abs(data) / 3))  # smoothness
    for i in range(steps + 1):
        angle = start_angle + (end_angle - start_angle) * i / steps
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        points.append((x, y))

    pygame.draw.polygon(surface, color, points)


background = pygame.Surface((800, 600))
background.fill(pygame.Color("#C0C0C0"))
manager = pygame_gui.UIManager((800, 600))

#Flight path
pygame.draw.rect(background,"#13C76D", [200, 100, 400, 350],0)


#Gauges
thrust_text = gauge_text.render("Thrust power", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
thruster_gauge = pygame.image.load('Firmware/Controller/Thrust-gauge.png')
pygame.draw.rect(background, (255, 0, 0), [700, 320, 40, 20], 0)
background.blit(thruster_gauge, (700,100))
background.blit(thrust_text, (672, 75))


pitch_text = gauge_text.render("Pitch", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
pitch_gauge = pygame.image.load('Firmware/Controller/Gauge_template_empty.png')
background.blit(pitch_gauge, (35,50))
pitch_gauge = pygame.image.load('Firmware/Controller/Gauge_pitch_text.png')
background.blit(pitch_gauge, (35,50))
background.blit(pitch_text, (78, 30))

roll_text = gauge_text.render("Roll", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
roll_gauge = pygame.image.load('Firmware/Controller/Gauge_template_empty.png')
background.blit(roll_gauge, (35,200))
roll_gauge = pygame.image.load('Firmware/Controller/Gauge_rol_text.png')
background.blit(roll_gauge, (35,200))
background.blit(roll_text, (80, 180))

heading_text = gauge_text.render("Heading", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
heading_gauge = pygame.image.load('Firmware/Controller/Gauge_template_empty.png')
background.blit(heading_gauge, (35,350))
heading_gauge = pygame.image.load('Firmware/Controller/Gauge_heading_text.png')
background.blit(heading_gauge, (35,350))
background.blit(heading_text, (67, 330))

#Bottom button creation
hello_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 500), (270, 100)), text='Thruster speed', manager=manager)
camera_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((265, 500), (273, 100)), text="Toggle Camera", manager=manager)
controll_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((530, 500), (273, 100)), text='Toggle Controller', manager=manager)



clock = pygame.time.Clock()
is_running = True


while is_running:
    time_delta = clock.tick(60)/1000.0

    #Gauge logic
   
    heading_gauge = pygame.image.load('Firmware/Controller/Gauge_template_empty.png')
    background.blit(heading_gauge, (35,350))
    if heading >=0:
        draw_wedge(background,(95, 410),59,heading,(255,0,0))
        if heading >= +180:
            heading -=359
    else:
        draw_wedge(background,(95, 410),59,heading,(255,0,0))
        if heading <= -180:
            heading +=359
    heading_gauge = pygame.image.load('Firmware/Controller/Gauge_heading_text.png')
    background.blit(heading_gauge, (35,350))
    background.blit(heading_text, (67, 330))


    max_height = 335
    bar_bottom_y = 340  # bottom of the gauge
    # calculate the current height of the thrust bar based on thrust value
    current_height = min(thrust, max_height)
    # calculate the top-left y coordinate so it grows upwards
    top_y = bar_bottom_y - current_height
    # draw the rectangle
    pygame.draw.rect(background, ("#C0C0C0"), [700, 320, 40, 0], 0)
    pygame.draw.rect(background, (255, 0, 0), [700, top_y-20, 40, current_height], 0)
    background.blit(thruster_gauge, (700,100))



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
                elif event.key == pygame.K_UP:
                    thrust += 1
                    print(f"Thrust up!\nThrust is now {thrust}")
                elif event.key == pygame.K_DOWN:
                    thrust -= 1
                    print(f"Thrust down!\nThrust is now {thrust}")
        
        #UI events
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == hello_button:
                thrust = thrust + 10
            if event.ui_element == camera_button:
                print('Camera is on')
            if event.ui_element == controll_button:
                print('Controller enabled')


        manager.process_events(event)


    manager.update(time_delta)


    window_surface.blit(background, (0, 0))

    manager.draw_ui(window_surface)


    pygame.display.update()