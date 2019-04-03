import tkinter as tk

from tkinter import ttk, filedialog
from PIL import Image, ImageTk


def center_window(root, size=0.7):
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    w, h = int(sw * size), int(sh * size)
    x = int((sw - w) / 2)
    y = int((sh - h) / 2)
    root.geometry("{}x{}+{}+{}".format(w, h, x, y))


class AutoScrollbar(ttk.Scrollbar):

    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            ttk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tk.TclError('Cannot use pack with this widget')

    def place(self, **kw):
        raise tk.TclError('Cannot use place with this widget')


class ImageViewer(ttk.Frame):

    def __init__(self, root):
        ttk.Frame.__init__(self, master=root)
        self.master.title('YAAT')
        center_window(root)

        root.config(menu=self.create_menu(root))

        vbar = AutoScrollbar(self.master, orient='vertical')
        hbar = AutoScrollbar(self.master, orient='horizontal')
        vbar.grid(row=0, column=1, sticky='ns')
        hbar.grid(row=1, column=0, sticky='we')
        vbar.configure(command=self.scroll_y)
        hbar.configure(command=self.scroll_x)

        self.canvas = tk.Canvas(self.master,
                                highlightthickness=0,
                                xscrollcommand=hbar.set,
                                yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()

        # Make the canvas resizable
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

        self.canvas.focus_set()  # catch key press
        self.canvas.bind('<Configure>', self.show_image)  # canvas is resized
        self.canvas.bind('<ButtonPress-2>', self.move_from)
        self.canvas.bind('<ButtonPress-3>', self.show_popup_menu)
        self.canvas.bind('<B2-Motion>', self.move_to)
        self.canvas.bind('<MouseWheel>', self.wheel)  # Windows, MacOS
        self.canvas.bind('<Button-5>', self.wheel)  # Linux, scroll down
        self.canvas.bind('<Button-4>', self.wheel)  # Linux, scroll up
        self.canvas.bind("<Key>", self.key_pressed)

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.oid = None
        self.sx, self.sy = None, None
        self.annos = []

        self.anno_color = "#00FF00"
        self.load_image("images/img_1.jpg")

    def on_button_press(self, event):
        if not self.oid:
            self.sx, self.sy = self.coords_inside(event)
            self.oid = self.canvas.create_rectangle(self.sx, self.sy, self.sx,
                                                    self.sy, outline=self.anno_color)

    def on_move_press(self, event):
        if self.oid:
            x, y = self.coords_inside(event)
            self.canvas.coords(self.oid, self.sx, self.sy, x, y)

    def on_button_release(self, event):
        # self.canvas.delete(self.rect)
        if self.oid:
            x1, y1, x2, y2 = self.canvas.coords(self.oid)
            print(self.coords_img(x1, y1), self.coords_img(x2, y2))
            self.annos.append(self.oid)
            self.oid = None

    def coords_img(self, cx, cy):
        """Convert canvas coordinates to image position"""
        s = self.scale
        bx, by, _, _ = self.canvas.bbox(self.container)
        ix, iy = int((cx - bx) / s), int((cy - by) / s)
        return ix, iy

    def coords_inside(self, event):
        x, y = self.coords(event)
        x1, y1, x2, y2 = self.canvas.bbox(self.container)
        return max(x1, min(x2, x)), max(y1, min(y2, y))

    def coords(self, event):
        """Convert event coordinates to canvas image coordinates"""
        return self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

    def key_pressed(self, event):
        print("key pressed:", event)
        if event.keycode == 46:  # delete
            if self.annos:
                self.canvas.delete(self.annos.pop())

    def load_image(self, path=None):
        if not path:
            filetypes = (("jpeg files", "*.jpg"), ("all files", "*.*"))
            path = filedialog.askopenfilename(initialdir=".",
                                              title="Select file",
                                              filetypes=filetypes)
        print("loading image", path)
        self.image = Image.open(path).convert('RGB')
        self.width, self.height = self.image.size
        self.scale = 3.0  # initial img scale
        self.delta = 1.3  # zoom factor
        self.container = self.canvas.create_rectangle(0, 0,
                                                      self.width * self.scale,
                                                      self.height * self.scale,
                                                      width=0)
        self.show_image()

    def create_menu(self, root):
        image = Image.open("icons/build.png")
        icon1 = ImageTk.PhotoImage(image)

        menubar = tk.Menu(root)

        editmenu = tk.Menu(menubar, tearoff=0)
        editmenu.icon1 = icon1
        editmenu.add_command(label="Cut", image=icon1, compound="left")
        editmenu.add_command(label="Copy")
        editmenu.add_command(label="Paste")
        menubar.add_cascade(label="Edit", menu=editmenu)

        colormenu = tk.Menu(menubar, tearoff=1)
        colormenu.add_command(label="red", command=lambda: self.select_color('#e74c3c'))
        colormenu.add_command(label="green", command=lambda: self.select_color('#52be80'))
        colormenu.add_command(label="blue", command=lambda: self.select_color('#5dade2'))
        menubar.add_cascade(label="Color", menu=colormenu)

        menubar.add_command(label="Quit!", command=self.quit)

        return menubar

    def create_popup_menu(self):
        menu = tk.Menu(self.master, tearoff=0)
        menu.add_command(label="Next")
        menu.add_command(label="Previous")
        menu.add_separator()
        menu.add_command(label="load", command=self.load_image)
        return menu

    def select_color(self, color):
        self.anno_color = color

    def quit(self):
        print("quitting...")
        self.master.destroy()
        print("done.")

    def show_popup_menu(self, event):
        menu = self.create_popup_menu()
        try:
            menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            menu.grab_release()

    def scroll_y(self, *args, **kwargs):
        """ Scroll canvas vertically and redraw the image """
        self.canvas.yview(*args, **kwargs)
        self.show_image()

    def scroll_x(self, *args, **kwargs):
        """ Scroll canvas horizontally and redraw the image """
        self.canvas.xview(*args, **kwargs)
        self.show_image()

    def move_from(self, event):
        """ Remember previous coordinates for scrolling with the mouse """
        self.canvas.scan_mark(event.x, event.y)

    def move_to(self, event):
        """ Drag (move) canvas to the new position """
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.show_image()

    def wheel(self, event):
        """ Zoom with mouse wheel """
        x, y = self.coords(event)
        bbox = self.canvas.bbox(self.container)  # get image area
        if not (bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]):
            return  # zoom only inside image area
        scale = 1.0

        if event.num == 5 or event.delta == -120:  # scroll down
            s = min(self.width, self.height)
            if int(s * self.scale) > 30:
                self.scale /= self.delta
                scale /= self.delta
        if event.num == 4 or event.delta == 120:  # scroll up
            s = min(self.canvas.winfo_width(), self.canvas.winfo_height())
            if s > self.scale:
                self.scale *= self.delta
                scale *= self.delta

        self.canvas.scale('all', x, y, scale, scale)
        self.show_image()

    def show_image(self, event=None):
        """ Show image on the Canvas """
        bbox1 = self.canvas.bbox(self.container)  # get image area

        # Remove 1 pixel shift at the sides of the bbox1
        bbox1 = (bbox1[0] + 1, bbox1[1] + 1, bbox1[2] - 1, bbox1[3] - 1)
        bbox2 = (self.canvas.canvasx(0),  # get visible area of the canvas
                 self.canvas.canvasy(0),
                 self.canvas.canvasx(self.canvas.winfo_width()),
                 self.canvas.canvasy(self.canvas.winfo_height()))
        bbox = [min(bbox1[0], bbox2[0]), min(bbox1[1], bbox2[1]),
                # get scroll region box
                max(bbox1[2], bbox2[2]), max(bbox1[3], bbox2[3])]

        # whole image in the visible area
        if bbox[0] == bbox2[0] and bbox[2] == bbox2[2]:
            bbox[0] = bbox1[0]
            bbox[2] = bbox1[2]

        # whole image in the visible area
        if bbox[1] == bbox2[1] and bbox[3] == bbox2[3]:
            bbox[1] = bbox1[1]
            bbox[3] = bbox1[3]
        self.canvas.configure(scrollregion=bbox)  # set scroll region

        # get coordinates (x1,y1,x2,y2) of the image tile
        x1 = max(bbox2[0] - bbox1[0], 0)
        y1 = max(bbox2[1] - bbox1[1], 0)
        x2 = min(bbox2[2], bbox1[2]) - bbox1[0]
        y2 = min(bbox2[3], bbox1[3]) - bbox1[1]

        # show image if it in the visible area
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:
            x = min(int(x2 / self.scale), self.width)
            y = min(int(y2 / self.scale), self.height)
            image = self.image.crop((int(x1 / self.scale), int(y1 / self.scale), x, y))
            imagetk = ImageTk.PhotoImage(
                image.resize((int(x2 - x1), int(y2 - y1))))
            imageid = self.canvas.create_image(max(bbox2[0], bbox1[0]),
                                               max(bbox2[1], bbox1[1]),
                                               anchor='nw', image=imagetk)
            self.canvas.lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # prevent garbage-collection


root = tk.Tk()
app = ImageViewer(root)
root.mainloop()
