import pygame
import math
import pygame_gui
import Input

#Diverse variables
thrust = 00
thrust_level = 100
heading = 90
pitch = 0
roll = 0
voltage = 2
current = 1
prev_voltage = 1
prev_current = 0
height = 10
text_gui = False
is_running = True


pygame.init()

#Initialisation function for readability
def gui_init():
    #Function relevant variables
    global thrust_text, thruster_gauge, battery_text, battery_voltage, battery_current, hello_button, \
        Gui_button, controll_button, window_surface, window, manager, gauge_text, Gui_button_text
    
    Gui_button_text = "Text GUI"
    gauge_text = pygame.font.SysFont("Arial", 16)
    pygame.display.set_caption("Drone GUI")
    window_surface = pygame.display.set_mode((800, 600))
    window = pygame.Surface((800, 600))
    window.fill(pygame.Color("#C0C0C0"))
    manager = pygame_gui.UIManager((800, 600))

    #Gauges init
    thrust_text = gauge_text.render("Thrust power", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    thruster_gauge= pygame.image.load('Firmware/Controller/Gui elements/Thrust-gauge.png')

    battery_text = gauge_text.render("Battery status:", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    battery_voltage = gauge_text.render(f"Voltage: {voltage}V", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)
    battery_current = gauge_text.render(f"Current: {current}A", True, (0, 0, 0)) # Text, Antialiasing, Color (RGB)

    #Bottom button creation
    hello_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 500), (270, 100)), text='Thruster speed', manager=manager)
    Gui_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((265, 500), (273, 100)), text=Gui_button_text, manager=manager)
    controll_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((530, 500), (273, 100)), text='Toggle Controller', manager=manager)




class Gauges:
    def __init__(self, surface, text, gauge_overlay_path, value, type):
        self.surface = surface
        self.gauge_background = pygame.image.load('Firmware/Controller/Gui elements/Gauge_template_empty.png')
        self.gauge_overlay = pygame.image.load(gauge_overlay_path)
        self.gauge_name = gauge_text.render(f"{text}", True, (0, 0, 0))
        self.value = value
        self.type = type

    def draw_wedge(self, center, radius, data, color=(255, 0, 0)):
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

        pygame.draw.polygon(self.surface, color, points)

    def draw_gauge (self,x,y):
        self.surface.blit(self.gauge_name,(x+30,y-20))
        self.surface.blit(self.gauge_background,(x,y))
        if(self.type == 2):
            self.draw_wedge((x+60,y+60),59,self.value)
        self.surface.blit(self.gauge_overlay,(x,y))

    def draw_text(self,x,y):
        self.surface.blit(self.gauge_name,(x,y))
        self.surface.blit(gauge_text.render(f": {self.value}", True, (0, 0, 0)),(x+60,y))




def eventhandler():
    global thrust, text_gui, is_running
    #Event handler
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False
    
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

        manager.process_events(event)

gui_init()
pitchG   = Gauges(window, "   Pitch",'Firmware/Controller/Gui elements/Gauge_pitch_text.png',pitch,0)
rollG    = Gauges(window, "    Roll",'Firmware/Controller/Gui elements/Gauge_roll_text.png',roll,1)
headingG = Gauges(window, "Heading",'Firmware/Controller/Gui elements/Gauge_heading_text.png',heading,2)




# Main loop
clock = pygame.time.Clock()

while is_running:
    time_delta = clock.tick(60)/1000.0

    #Redraws frame
    pygame.draw.rect(window,"#C0C0C0", [0, 0, 800, 600],0)
    if (text_gui):
        pitchG.draw_text(35,50)
        rollG.draw_text(35,70)
        headingG.draw_text(35,90)
    else:
        pitchG.draw_gauge(35,50)
        rollG.draw_gauge(35,200)
        headingG.draw_gauge(35,350)

    eventhandler()

    manager.update(time_delta)
    window_surface.blit(window, (0, 0))
    manager.draw_ui(window_surface)
    pygame.display.update()