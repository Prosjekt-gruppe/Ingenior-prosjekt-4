import tkinter as tk
from PIL import Image, ImageTk
import cv2
cap = cv2.VideoCapture(0) 

camera_on = False 
canvas_img_obj = None

# --- Functions ---
def update_frame():
    if camera_on:
        ret, frame = cap.read()
        if ret:
            frame = cv2.flip(frame, 1)  # Optional mirror
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img = img.resize((800, 500))

            global canvas_img_obj
            canvas_img_obj = ImageTk.PhotoImage(img)
            canvas.create_image(0, 0, anchor="nw", image=canvas_img_obj)

    gui.after(30, update_frame)  # Keep looping regardless

def toggle_camera():
    global camera_on
    camera_on = not camera_on
    button3.config(text="Stop Camera" if camera_on else "Start Camera")
    if camera_on == False:
        canvas.delete("all")

rect_id = None  # Global to track the square

def toggle_square():
    global rect_id
    if rect_id is None:
        # Draw square and save ID
        x1, y1 = 300, 350  # top-left corner
        width, height = 150, 80  # rectangle size
        x2, y2 = x1 + width, y1 + height
        rect_id = canvas.create_rectangle(x1, y1, x2, y2, fill="blue", outline="black", width=2)
    else:
        # Delete square and reset ID
        canvas.delete(rect_id)
        rect_id = None


gui = tk.Tk()
gui.title("Drone gui")
gui.geometry("800x750")


canvas = tk.Canvas(gui, width=800, height=800, bg="white")
canvas.place(x = 0,y =0)

grid_frame = tk.Frame(gui, bg="gray", height=200)
grid_frame.pack(side="bottom", fill="x")


target_x = 100  # target center position inside canvas


# Put buttons inside grid_frame, NOT bottom_frame
title_label = tk.Label(
    grid_frame,
    text="Control Panel",
    font=("Arial", 16, "bold"),
    bg="lightgray",        # Background color of the label
    fg="white",           # Optional: text color
    anchor="center"       # Align text center if width expands
)
button1 = tk.Button(grid_frame, text="Exit", width=20, command=gui.destroy)
button2 = tk.Button(grid_frame, text="Empty", width=20,)
button3 = tk.Button(grid_frame, text="Start Camera", command=toggle_camera, width=20)
button4 = tk.Button(grid_frame, text="pitch", width=20, command=toggle_square)


title_label.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(10, 5))
button1.grid(row=0, column=0, pady=20, padx=10)
button2.grid(row=0, column=1, pady=20, padx=10)
button3.grid(row=0, column=2, pady=20, padx=10)
button4.grid(row=0, column=3, pady=20, padx=10)
grid_frame.columnconfigure([0, 1, 2], weight=1)

update_frame()
gui.mainloop()

# --- Cleanup ---
cap.release()