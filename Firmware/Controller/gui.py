import pygame
import pygame_gui
import os


pygame.init()

thrust = 00
pygame.display.set_caption("Drone GUI")

window_surface = pygame.display.set_mode((800, 600))


background = pygame.Surface((800, 600))
background.fill(pygame.Color("#C0C0C0"))
manager = pygame_gui.UIManager((800, 600))

#Flight path
pygame.draw.rect(background,"#13C76D", [200, 100, 400, 350],0)


#Gauges
thruster_gauge = pygame.image.load('Firmware/Controller/Thrust-gauge.png')
pygame.draw.rect(background, (255, 0, 0), [700, 320, 40, 20], 0)
background.blit(thruster_gauge, (700,100))


pitch_gauge = pygame.image.load('Firmware/Controller/Gauge_template.png')
background.blit(pitch_gauge, (35,50))
pygame.draw.circle(background,"#000000",[35,50], 5,2)

roll_gauge = pygame.image.load('Firmware/Controller/Gauge_template.png')
background.blit(roll_gauge, (35,200))

heading_gauge = pygame.image.load('Firmware/Controller/Gauge_template.png')
background.blit(heading_gauge, (35,350))


#Bottom button creation
hello_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 500), (270, 100)), text='Thruster speed', manager=manager)
camera_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((265, 500), (273, 100)), text="Toggle Camera", manager=manager)
controll_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((530, 500), (273, 100)), text='Toggle Controller', manager=manager)



clock = pygame.time.Clock()
is_running = True


while is_running:
    time_delta = clock.tick(60)/1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False


        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == hello_button:
                thrust = thrust + 10
                max_height = 335
                bar_bottom_y = 340  # bottom of the gauge
                    # calculate the current height of the thrust bar based on thrust value
                current_height = min(thrust, max_height)
                # calculate the top-left y coordinate so it grows upwards
                top_y = bar_bottom_y - current_height
                # draw the rectangle
                if thrust > 200:
                    pygame.draw.rect(background, ("#C0C0C0"), [700, top_y-20, 40, current_height], 0)
                    background.blit(thruster_gauge, (700,100))
                    thrust = 0
                else:
                    pygame.draw.rect(background, (255, 0, 0), [700, top_y-20, 40, current_height], 0)
                    background.blit(thruster_gauge, (700,100))
                
            if event.ui_element == camera_button:
                print('Camera is on')
            if event.ui_element == controll_button:
                print('Controller enabled')


        manager.process_events(event)


    manager.update(time_delta)


    window_surface.blit(background, (0, 0))

    manager.draw_ui(window_surface)


    pygame.display.update()