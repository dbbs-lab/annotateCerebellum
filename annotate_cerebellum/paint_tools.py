"""
Contains the controller classes used for the user interface to modify the cerebellar volumetric
annotations.
"""
import numpy as np
from os.path import join
from tkinter import Tk, Frame, Button, Label, Scale, RIDGE, RAISED, SUNKEN, HORIZONTAL
from PIL import ImageTk, Image
from annotate_cerebellum.canvas_image import CanvasImage
from annotate_cerebellum.annotation_image import AnnotationImage
from annotate_cerebellum.utils import draw_2d_line


class PaintTools:
    """
    Class of the controller of the user application to modify volumetric cerebellar annotations.
    Contains also the view of the paint toolbox.
    """

    def __init__(self, placeholder, icon_folder, canvas, annotations, axis=0):
        """
        Initialize the controller and the view of the paint toolbox for the annotation correction
        application.

        :param Widget placeholder: Parent widget holding the CanvasImage
        :param str icon_folder: Folder containing the icons of the painting toolbox.
        :param Widget canvas: View of the displayed annotations
        :param annotations: Model of the displayed annotations
        """
        self.paint_tools = Frame(placeholder, relief=RIDGE, borderwidth=2)
        self.canvas = canvas
        self.annotations = annotations

        self.old_x = None
        self.old_y = None
        self.dx = 0
        self.dy = 0
        self.eraser_on = False
        self.active_button = None
        self.active_color = None
        self.current_key = None

        # pen button
        pen_image = Image.open(join(icon_folder, "pen.png"))
        pen_image = pen_image.convert("RGB")
        pen_image = pen_image.resize((50, 50), Image.LANCZOS)
        self.pen_image = ImageTk.PhotoImage(pen_image)
        self.pen_button = Button(self.paint_tools, padx=6, bg="white", image=self.pen_image,
                                 command=self.use_pen)
        self.pen_button.grid(row=0, column=0, padx=10, pady=10, sticky='nw')

        # fill button
        fill_image = Image.open(join(icon_folder, "fill.png"))
        fill_image = fill_image.convert("RGB")
        fill_image = fill_image.resize((50, 50), Image.LANCZOS)
        self.fill_image = ImageTk.PhotoImage(fill_image)
        self.fill_button = Button(self.paint_tools, padx=6, bg="white", image=self.fill_image,
                                  command=self.use_fill)
        self.fill_button.grid(row=0, column=1, padx=10, pady=10, sticky='nw')

        # revert button
        eraser_image = Image.open(join(icon_folder, "eraser.png"))
        eraser_image = eraser_image.convert("RGB")
        eraser_image = eraser_image.resize((50, 50), Image.LANCZOS)
        self.eraser_image = ImageTk.PhotoImage(eraser_image)
        self.eraser_button = Button(self.paint_tools, padx=6, bg="white", image=self.eraser_image,
                                    command=self.use_eraser)
        self.eraser_button.grid(row=1, column=0, padx=10, pady=10, sticky='nw')

        # move button
        move_image = Image.open(join(icon_folder, "move.png"))
        move_image = move_image.convert("RGB")
        move_image = move_image.resize((50, 50), Image.LANCZOS)
        self.move_image = ImageTk.PhotoImage(move_image)
        self.move_button = Button(self.paint_tools, padx=6, bg="white", image=self.move_image,
                                  command=self.use_move)
        self.move_button.grid(row=1, column=1, padx=10, pady=10, sticky='nw')

        # slice position
        slice_label = Label(self.paint_tools, text="Id slice:", font=('Arial', 10, 'bold'))
        slice_label.grid(row=0, column=2, padx=10, sticky='w')
        self.slice_scale = Scale(self.paint_tools,
                                 from_=self.annotations.ids[axis, 0],
                                 to=self.annotations.ids[axis, 1],
                                 orient=HORIZONTAL, length=150, command=self.change_slice)
        self.slice_scale.set(self.annotations.slice_pos)
        self.slice_scale.grid(row=0, column=3, padx=10, pady=10, columnspan=3, sticky='nswe')

        # colors
        self.red_button = Button(self.paint_tools, padx=6, bg="red", text="GL",
                                 command=self.set_gl)
        self.red_button.grid(row=1, column=2, padx=10, pady=10, sticky='nw')
        self.green_button = Button(self.paint_tools, padx=6, bg="green", text="ML",
                                   command=self.set_ml)
        self.green_button.grid(row=1, column=3, padx=10, pady=10, sticky='nw')
        self.blue_button = Button(self.paint_tools, padx=6, bg="blue", text="Fib",
                                  command=self.set_fib)
        self.blue_button.grid(row=1, column=4, padx=10, pady=10, sticky='nw')
        self.black_button = Button(self.paint_tools, padx=6, bg="black", text="Out", fg='white',
                                   command=self.set_out)
        self.black_button.grid(row=1, column=5, padx=10, pady=10, sticky='nw')

        # save button
        save_image = Image.open(join(icon_folder, "save.png"))
        save_image = save_image.convert("RGB")
        save_image = save_image.resize((50, 50), Image.LANCZOS)
        self.save_image = ImageTk.PhotoImage(save_image)
        self.save_button = Button(self.paint_tools, padx=6, bg="white", image=self.save_image,
                                  command=self.save)
        self.save_button.grid(row=0, column=6, padx=10, pady=10, sticky='nw')

        # revert button
        revert_image = Image.open(join(icon_folder, "revert.png"))
        revert_image = revert_image.convert("RGB")
        revert_image = revert_image.resize((50, 50), Image.LANCZOS)
        self.revert_image = ImageTk.PhotoImage(revert_image)
        self.revert_button = Button(self.paint_tools, padx=6, bg="white", image=self.revert_image,
                                    command=self.revert)
        self.revert_button.grid(row=1, column=6, padx=10, pady=10, sticky='nw')

    def grid(self, **kw):
        """
        Put the Paint tools widget on the parent widget.
        """
        self.paint_tools.grid(**kw)  # place CanvasImage widget on the grid
        self.paint_tools.grid(sticky='nw')  # make frame container sticky
        self.paint_tools.rowconfigure(0, weight=1)  # make canvas expandable
        self.paint_tools.columnconfigure(0, weight=1)

    def use_pen(self):
        """
        Activate the pen tool.
        """
        self.__activate_button(self.pen_button)
        self.canvas.canvas.bind('<ButtonRelease-1>', self.__reset)
        self.canvas.canvas.bind('<B1-Motion>', self.paint)

    def use_fill(self):
        """
        Activate the fill tool.
        """
        self.__activate_button(self.fill_button)
        self.canvas.canvas.bind('<ButtonRelease-1>', self.fill)

    def use_eraser(self):
        """
        Activate the eraser tool.
        """
        self.__activate_button(self.eraser_button)
        self.canvas.canvas.bind('<ButtonRelease-1>', self.__reset)
        self.canvas.canvas.bind('<B1-Motion>', self.erase)

    def change_slice(self, coronal_pos):
        """
        Change the slice displayed based on the provided coronal position.
        """
        self.annotations.change_slice(int(coronal_pos))
        self.canvas.update_image(self.annotations.picRGB)

    def __change_color(self, some_button):
        """
        Change the active group or color button.

        :param some_button: Button to activate
        """
        if self.active_color is not None:
            self.active_color.config(relief=RAISED)
        some_button.config(relief=SUNKEN)
        self.active_color = some_button

    def set_gl(self):
        """
        Set the active group or color button to granular layer.
        """
        self.__change_color(self.red_button)
        self.current_key = "gl"

    def set_ml(self):
        """
        Set the active group or color button to molecular layer.
        """
        self.__change_color(self.green_button)
        self.current_key = "mol"

    def set_fib(self):
        """
        Set the active group or color button to fiber tracts.
        """
        self.__change_color(self.blue_button)
        self.current_key = "fib"

    def set_out(self):
        """
        Set the active group or color button to the outside.
        """
        self.__change_color(self.black_button)
        self.current_key = "out"

    def __activate_button(self, some_button):
        """
        Change the active tool button.

        :param some_button: Button to activate
        """
        if self.active_button is not None:
            self.active_button.config(relief=RAISED)
        some_button.config(relief=SUNKEN)
        self.active_button = some_button
        self.canvas.canvas.unbind('<ButtonPress-1>')
        self.canvas.canvas.unbind('<B1-Motion>')
        self.canvas.canvas.unbind('<ButtonRelease-1>')
        self.old_x = None
        self.old_y = None

    def use_move(self):
        """
        Activate the move tool.
        """
        self.__activate_button(self.move_button)
        self.canvas.canvas.bind('<ButtonPress-1>',
                                lambda event: self.canvas.canvas.scan_mark(event.x, event.y))
        self.canvas.canvas.bind("<B1-Motion>", self.canvas.move_to)

    def __reset(self, _):
        self.old_x, self.old_y = None, None

    def paint(self, event):
        """
        Draw all the voxels between the current and previously recorded position of the mouse
        cursor on the view and update the annotations.

        :param event: Position of the mouse cursor when the function is called.
        """
        offset_x, offset_y = self.canvas.get_offsets()
        if self.old_x and self.old_y and self.current_key:
            voxels_to_update = draw_2d_line((self.old_x + offset_x) / self.canvas.imscale,
                                            (self.old_y + offset_y) / self.canvas.imscale,
                                            (event.x + offset_x) / self.canvas.imscale,
                                            (event.y + offset_y) / self.canvas.imscale) - 1
            voxels_to_update = np.array([voxels_to_update[:, 1], voxels_to_update[:, 0]]).T
            # Update RGB
            self.annotations.update_slice(voxels_to_update, self.current_key)
            self.canvas.update_image(self.annotations.picRGB)
        self.old_x = event.x
        self.old_y = event.y

    def erase(self, event):
        """
        Revert the changes applied to the images and the annotation between the current and
        previously recorded position of the mouse cursor.

        :param event: Position of the mouse cursor when the function is called.
        """
        offset_x, offset_y = self.canvas.get_offsets()
        if self.old_x and self.old_y:
            voxels_to_update = draw_2d_line((self.old_x + offset_x) / self.canvas.imscale,
                                            (self.old_y + offset_y) / self.canvas.imscale,
                                            (event.x + offset_x) / self.canvas.imscale,
                                            (event.y + offset_y) / self.canvas.imscale) - 1
            voxels_to_update = np.array([voxels_to_update[:, 1], voxels_to_update[:, 0]]).T
            # Update RGB
            self.annotations.revert_voxels(voxels_to_update)
            self.canvas.update_image(self.annotations.picRGB)
        self.old_x = event.x
        self.old_y = event.y

    def fill(self, event):
        """
        Set the value of all the pixels surrounding the current position of the mouse cursor that
        match the group at that position.

        :param event: Position of the mouse cursor when the function is called.
        """
        offset_x, offset_y = self.canvas.get_offsets()
        if self.current_key:
            self.annotations.fill(
                np.asarray(np.rint([(event.y + offset_y) / self.canvas.imscale - 1,
                                    (event.x + offset_x) / self.canvas.imscale - 1]),
                           dtype=int),
                self.current_key)
            self.canvas.update_image(self.annotations.picRGB)

    def save(self):
        """
        Save the changes applied to the annotations. Update the backup.
        """
        self.annotations.apply_changes()

    def revert(self):
        """
        Revert the last changes applied to the annotations.
        """
        self.annotations.revert_slice()
        self.canvas.update_image(self.annotations.picRGB)


class PaintAnnotations:
    """
    Class to load the user application to modify volumetric cerebellar annotations.
    """

    def __init__(self, annotation, nissl, dict_reg_ids, axis=0, icon_folder="icons", backup=None):
        """
        Initialize the application.

        :param annotation: np.ndarray annotation volume
        :param nissl: np.ndarray Nissl volume
        :param dict_reg_ids: dictionary linking cerebellum layers to their region ids.
        :param icon_folder: folder location for the icons used in the app
        """
        self.root = Tk()
        self.root.title("Mouse Brain Paint")
        self.root.geometry('800x600')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=7)

        self.annotations = AnnotationImage(annotation, dict_reg_ids, nissl, axis, backup)
        self.canvas = CanvasImage(self.root, self.annotations.picRGB)
        self.canvas.grid(row=1, column=0)  # show widget
        self.toolbox = PaintTools(self.root, icon_folder, self.canvas, self.annotations, axis)
        self.toolbox.grid(row=0, column=0)
        self.root.mainloop()

    def get_annotations(self):
        """
        Getter for the annotations volume.
        """
        return self.annotations.annotation
