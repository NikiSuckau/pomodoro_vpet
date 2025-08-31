import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

# Action to output filename mapping
ACTION_TO_FILENAME = {
    "walk 1": "0.png",
    "walk 2": "1.png",
    "happy 1": "3.png",
    "happy 2": "7.png",
    "attack 1": "6.png",
    "attack 2": "11.png",
}
ACTIONS = list(ACTION_TO_FILENAME.keys())


class SpriteSlicerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sprite Slicer GUI")
        self.geometry("800x600")
        self.sheet_img = None
        self.tk_img = None
        self.sprite_width = tk.IntVar(value=48)
        self.sprite_height = tk.IntVar(value=48)
        self.sheet_path = tk.StringVar()
        self.sliced_images = []
        self.rows = 0
        self.cols = 0
        self.action_assignments = {a: None for a in ACTIONS}

        self.build_main_frame()

    def build_main_frame(self):
        frame = ttk.Frame(self)
        frame.pack(side=tk.TOP, fill=tk.X, padx=8, pady=8)

        ttk.Label(frame, text="Sprite Width:").pack(side=tk.LEFT)
        ttk.Entry(frame, textvariable=self.sprite_width, width=5).pack(side=tk.LEFT)
        ttk.Label(frame, text="Sprite Height:").pack(side=tk.LEFT)
        ttk.Entry(frame, textvariable=self.sprite_height, width=5).pack(side=tk.LEFT)
        ttk.Button(frame, text="Open Sheet", command=self.load_sheet).pack(side=tk.LEFT)
        self.sheet_label = ttk.Label(frame, text="No file chosen")
        self.sheet_label.pack(side=tk.LEFT, padx=8)

        self.canvas = tk.Canvas(self, width=480, height=480)
        self.canvas.pack(pady=10)

        self.next_button = ttk.Button(
            self, text="Preview Slices", command=self.preview_slices
        )
        self.next_button.pack(pady=5)

    def load_sheet(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                ("All files", "*"),
            ]
        )
        if not path:
            return
        self.sheet_path.set(path)
        self.sheet_label.config(text=os.path.basename(path))
        try:
            self.sheet_img = Image.open(path)
            self.tk_img = ImageTk.PhotoImage(self.sheet_img.resize((480, 480)))
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            self.sheet_img = None
            self.tk_img = None

    def preview_slices(self):
        if not self.sheet_img:
            messagebox.showerror("No image", "You must load a sprite sheet first.")
            return
        sw, sh = self.sprite_width.get(), self.sprite_height.get()
        w, h = self.sheet_img.size
        self.cols = w // sw
        self.rows = h // sh
        # Draw grid
        self.canvas.delete("all")
        self.tk_img = ImageTk.PhotoImage(self.sheet_img.resize((480, 480)))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
        scale_x = 480 / w
        scale_y = 480 / h
        for r in range(self.rows):
            y = int(r * sh * scale_y)
            self.canvas.create_line(0, y, 480, y, fill="red")
        for c in range(self.cols):
            x = int(c * sw * scale_x)
            self.canvas.create_line(x, 0, x, 480, fill="red")
        self.canvas.create_line(0, 480 - 1, 480 - 1, 480 - 1, fill="red")
        self.canvas.create_line(480 - 1, 0, 480 - 1, 480 - 1, fill="red")
        # Prep slice images
        self.sliced_images = []
        for r in range(self.rows):
            for c in range(self.cols):
                left = c * sw
                upper = r * sh
                right = left + sw
                lower = upper + sh
                sprite = self.sheet_img.crop((left, upper, right, lower))
                self.sliced_images.append(sprite)
        # Move to action assignment UI
        self.after(500, self.action_assignment_ui)

    def action_assignment_ui(self):
        self.canvas.pack_forget()
        if hasattr(self, "action_frame"):
            self.action_frame.destroy()
        self.action_frame = ttk.Frame(self)
        self.action_frame.pack(pady=20)
        self.current_idx = 0
        self.sprite_label = ttk.Label(self.action_frame)
        self.sprite_label.pack()
        btn_frame = ttk.Frame(self.action_frame)
        btn_frame.pack(pady=10)
        self.action_btns = []
        for action in ACTIONS:
            btn = ttk.Button(
                btn_frame, text=action, command=lambda a=action: self.assign_action(a)
            )
            btn.pack(side=tk.LEFT, padx=4)
            self.action_btns.append(btn)
        self.skip_btn = ttk.Button(btn_frame, text="Skip", command=self.next_sprite)
        self.skip_btn.pack(side=tk.LEFT, padx=4)
        self.status_label = ttk.Label(self.action_frame, text="")
        self.status_label.pack()
        self.display_sprite()

    def display_sprite(self):
        if self.current_idx >= len(self.sliced_images):
            self.status_label.config(
                text="All sprites processed! Saving assigned actions..."
            )
            self.save_sprites()
            return
        sprite = self.sliced_images[self.current_idx]
        sprite_img = ImageTk.PhotoImage(sprite.resize((96, 96)))
        self.sprite_label.config(image=sprite_img)
        self.sprite_label.image = sprite_img
        used = set(self.action_assignments.values())
        for i, action in enumerate(ACTIONS):
            if self.current_idx in used:
                self.action_btns[i]["state"] = tk.DISABLED
            else:
                if (
                    action in self.action_assignments
                    and self.action_assignments[action] is not None
                ):
                    self.action_btns[i]["state"] = tk.DISABLED
                else:
                    self.action_btns[i]["state"] = tk.NORMAL
        self.status_label.config(
            text=f"Sprite {self.current_idx+1} / {len(self.sliced_images)}"
        )

    def assign_action(self, action):
        if self.action_assignments[action] is not None:
            messagebox.showerror(
                "Already assigned", f"Action {action} already has a sprite assigned."
            )
            return
        used = set(self.action_assignments.values())
        if self.current_idx in used:
            messagebox.showerror(
                "Already used", f"This sprite is already assigned to another action."
            )
            return
        self.action_assignments[action] = self.current_idx
        self.next_sprite()

    def next_sprite(self):
        self.current_idx += 1
        self.display_sprite()

    def save_sprites(self):
        # Ask user for export options
        choice = tk.messagebox.askquestion(
            "Export Options",
            "How would you like to export your sprites?\n\nYes = PNG files only\nNo = .ZIP only\nCancel = Both",
            icon='question', type='yesnocancel'
        )
        if choice == 'cancel':
            export_png = True
            export_zip = True
        elif choice == 'yes':
            export_png = True
            export_zip = False
        elif choice == 'no':
            export_png = False
            export_zip = True
        else:
            messagebox.showinfo("Cancelled", "Export cancelled.")
            self.quit()
            return

        saved_files = []
        outdir = None
        if export_png or export_zip:
            outdir = filedialog.askdirectory(title="Choose output directory for PNGs")
            if not outdir:
                messagebox.showinfo("Cancelled", "Save cancelled.")
                self.quit()
                return
        if export_png:
            for action, idx in self.action_assignments.items():
                if idx is not None and 0 <= idx < len(self.sliced_images):
                    out_path = os.path.join(outdir, ACTION_TO_FILENAME[action])
                    self.sliced_images[idx].save(out_path, format="PNG")
                    saved_files.append(out_path)
            msg = "Saved sprites for actions: " + ", ".join(
                [a for a, idx in self.action_assignments.items() if idx is not None]
            )
            messagebox.showinfo("Saved", msg)
        if export_zip:
            import zipfile
            zip_path = filedialog.asksaveasfilename(
                title="Export as zip...",
                defaultextension=".zip",
                filetypes=[("Zip files", "*.zip")],
            )
            if zip_path:
                try:
                    with zipfile.ZipFile(zip_path, "w") as zipf:
                        # If user only wants zip but not png, create temp files
                        if not export_png:
                            for action, idx in self.action_assignments.items():
                                if idx is not None and 0 <= idx < len(self.sliced_images):
                                    tmp_path = os.path.join(outdir, ACTION_TO_FILENAME[action])
                                    self.sliced_images[idx].save(tmp_path, format="PNG")
                                    saved_files.append(tmp_path)
                        # Ensure all 0.png to 11.png are present, fill missing with walk 1
                        # 1. Map action assignments to output files
                        all_filenames = [f"{i}.png" for i in range(12)]
                        walk1_idx = self.action_assignments.get("walk 1")
                        walk1_sprite = None
                        if walk1_idx is not None and 0 <= walk1_idx < len(self.sliced_images):
                            walk1_sprite = self.sliced_images[walk1_idx]
                        img_map = {ACTION_TO_FILENAME[a]: idx for a, idx in self.action_assignments.items() if idx is not None}
                        # 2. Write/prepare all images
                        temp_files_to_remove = []
                        for fname in all_filenames:
                            fpath = os.path.join(outdir, fname)
                            if fname not in img_map:
                                # Not assigned, fill using walk 1
                                if walk1_sprite is not None:
                                    walk1_sprite.save(fpath, format="PNG")
                                    temp_files_to_remove.append(fpath)
                            # else, already saved in export_png or above
                        # Now zip them all
                        for fname in all_filenames:
                            fpath = os.path.join(outdir, fname)
                            if os.path.exists(fpath):
                                zipf.write(fpath, fname)
                        # Cleanup temp files if only zipped, not exported as png
                        if not export_png:
                            for f in temp_files_to_remove:
                                try:
                                    os.remove(f)
                                except Exception:
                                    pass
                    messagebox.showinfo("Exported", f"Sprites exported to zip: {zip_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to export zip: {e}")
        self.quit()


if __name__ == "__main__":
    app = SpriteSlicerGUI()
    app.mainloop()
