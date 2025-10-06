import tkinter as tk
from tkinter import messagebox, filedialog
import json
import math

class DrawingGrid:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("512x512 Drawing Grid")
        self.root.resizable(True, True)
        
        self.grid_size = 512
        self.cell_size = 2
        
        self.canvas_width = self.grid_size * self.cell_size
        self.canvas_height = self.grid_size * self.cell_size
        
        self.drawn_cells = set()
        self.current_tool = "pen"
        self.brush_width = 1
        
        # For line and circle drawing
        self.temp_shape = None
        self.start_pos = None
        
        self.setup_ui()
        
    def setup_ui(self):
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=5)
        
        # Tool buttons
        tool_frame = tk.Frame(control_frame)
        tool_frame.pack(side=tk.LEFT)
        
        pen_btn = tk.Button(tool_frame, text="Pen", command=self.select_pen, 
                           bg="black", fg="white", width=8)
        pen_btn.pack(side=tk.LEFT, padx=2)
        
        eraser_btn = tk.Button(tool_frame, text="Eraser", command=self.select_eraser, 
                              bg="lightgray", width=8)
        eraser_btn.pack(side=tk.LEFT, padx=2)
        
        line_btn = tk.Button(tool_frame, text="Line", command=self.select_line, 
                            bg="blue", fg="white", width=8)
        line_btn.pack(side=tk.LEFT, padx=2)
        
        circle_btn = tk.Button(tool_frame, text="Circle", command=self.select_circle, 
                              bg="purple", fg="white", width=8)
        circle_btn.pack(side=tk.LEFT, padx=2)
        
        # Width control
        width_frame = tk.Frame(control_frame)
        width_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(width_frame, text="Width:").pack(side=tk.LEFT)
        self.width_scale = tk.Scale(width_frame, from_=1, to=20, orient=tk.HORIZONTAL, 
                                    command=self.change_width, length=100)
        self.width_scale.set(1)
        self.width_scale.pack(side=tk.LEFT, padx=5)
        
        # Action buttons
        action_frame = tk.Frame(control_frame)
        action_frame.pack(side=tk.LEFT)
        
        save_btn = tk.Button(action_frame, text="Save", command=self.save_drawing, 
                            bg="green", fg="white", width=8)
        save_btn.pack(side=tk.LEFT, padx=2)
        
        clear_btn = tk.Button(action_frame, text="Clear", command=self.clear_drawing, 
                             bg="red", fg="white", width=8)
        clear_btn.pack(side=tk.LEFT, padx=2)
        
        self.canvas = tk.Canvas(self.root, width=self.canvas_width, height=self.canvas_height, 
                               bg="white", bd=1, relief="solid")
        self.canvas.pack(pady=5)
        
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
    def get_cell_coords(self, x, y):
        cell_x = x // self.cell_size
        cell_y = y // self.cell_size
        
        if 0 <= cell_x < self.grid_size and 0 <= cell_y < self.grid_size:
            return cell_x, cell_y
        return None
    
    def draw_cell(self, cell_x, cell_y):
        # Draw cells based on brush width
        half_width = self.brush_width // 2
        for dx in range(-half_width, half_width + 1):
            for dy in range(-half_width, half_width + 1):
                cx, cy = cell_x + dx, cell_y + dy
                if 0 <= cx < self.grid_size and 0 <= cy < self.grid_size:
                    x1 = cx * self.cell_size
                    y1 = cy * self.cell_size
                    x2 = x1 + self.cell_size
                    y2 = y1 + self.cell_size
                    
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="black", outline="black")
                    self.drawn_cells.add((cx, cy))
    
    def erase_cell(self, cell_x, cell_y):
        # Erase cells based on brush width
        half_width = self.brush_width // 2
        for dx in range(-half_width, half_width + 1):
            for dy in range(-half_width, half_width + 1):
                cx, cy = cell_x + dx, cell_y + dy
                if 0 <= cx < self.grid_size and 0 <= cy < self.grid_size:
                    x1 = cx * self.cell_size
                    y1 = cy * self.cell_size
                    x2 = x1 + self.cell_size
                    y2 = y1 + self.cell_size
                    
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="white")
                    self.drawn_cells.discard((cx, cy))
    
    def draw_line_cells(self, x0, y0, x1, y1):
        """Bresenham's line algorithm to get all cells in a line"""
        cells = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        while True:
            cells.append((x, y))
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        return cells
    
    def draw_circle_cells(self, cx, cy, radius):
        """Midpoint circle algorithm to get all cells in a circle"""
        cells = set()
        x = radius
        y = 0
        err = 0
        
        while x >= y:
            # Add all 8 octants
            points = [
                (cx + x, cy + y), (cx + y, cy + x),
                (cx - y, cy + x), (cx - x, cy + y),
                (cx - x, cy - y), (cx - y, cy - x),
                (cx + y, cy - x), (cx + x, cy - y)
            ]
            
            for px, py in points:
                if 0 <= px < self.grid_size and 0 <= py < self.grid_size:
                    cells.add((px, py))
            
            if err <= 0:
                y += 1
                err += 2 * y + 1
            if err > 0:
                x -= 1
                err -= 2 * x + 1
        
        return list(cells)
    
    def on_click(self, event):
        coords = self.get_cell_coords(event.x, event.y)
        if coords:
            cell_x, cell_y = coords
            
            if self.current_tool == "pen":
                self.draw_cell(cell_x, cell_y)
            elif self.current_tool == "eraser":
                self.erase_cell(cell_x, cell_y)
            elif self.current_tool in ["line", "circle"]:
                self.start_pos = (cell_x, cell_y)
    
    def on_drag(self, event):
        coords = self.get_cell_coords(event.x, event.y)
        if coords:
            cell_x, cell_y = coords
            
            if self.current_tool == "pen":
                self.draw_cell(cell_x, cell_y)
            elif self.current_tool == "eraser":
                self.erase_cell(cell_x, cell_y)
            elif self.current_tool == "line" and self.start_pos:
                # Draw preview line
                if self.temp_shape:
                    self.canvas.delete(self.temp_shape)
                x0, y0 = self.start_pos
                self.temp_shape = self.canvas.create_line(
                    x0 * self.cell_size, y0 * self.cell_size,
                    cell_x * self.cell_size, cell_y * self.cell_size,
                    fill="gray", width=2
                )
            elif self.current_tool == "circle" and self.start_pos:
                # Draw preview circle
                if self.temp_shape:
                    self.canvas.delete(self.temp_shape)
                x0, y0 = self.start_pos
                radius = int(math.sqrt((cell_x - x0)**2 + (cell_y - y0)**2))
                x1 = (x0 - radius) * self.cell_size
                y1 = (y0 - radius) * self.cell_size
                x2 = (x0 + radius) * self.cell_size
                y2 = (y0 + radius) * self.cell_size
                self.temp_shape = self.canvas.create_oval(
                    x1, y1, x2, y2, outline="gray", width=2
                )
    
    def on_release(self, event):
        coords = self.get_cell_coords(event.x, event.y)
        if coords and self.start_pos:
            cell_x, cell_y = coords
            
            if self.current_tool == "line":
                # Draw the line
                if self.temp_shape:
                    self.canvas.delete(self.temp_shape)
                    self.temp_shape = None
                
                x0, y0 = self.start_pos
                cells = self.draw_line_cells(x0, y0, cell_x, cell_y)
                for cx, cy in cells:
                    self.draw_cell(cx, cy)
                
            elif self.current_tool == "circle":
                # Draw the circle
                if self.temp_shape:
                    self.canvas.delete(self.temp_shape)
                    self.temp_shape = None
                
                x0, y0 = self.start_pos
                radius = int(math.sqrt((cell_x - x0)**2 + (cell_y - y0)**2))
                cells = self.draw_circle_cells(x0, y0, radius)
                for cx, cy in cells:
                    self.draw_cell(cx, cy)
            
            self.start_pos = None
    
    def select_pen(self):
        self.current_tool = "pen"
    
    def select_eraser(self):
        self.current_tool = "eraser"
    
    def select_line(self):
        self.current_tool = "line"
    
    def select_circle(self):
        self.current_tool = "circle"
    
    def change_width(self, value):
        self.brush_width = int(value)
    
    def clear_drawing(self):
        self.canvas.delete("all")
        self.drawn_cells.clear()
        self.temp_shape = None
        self.start_pos = None
    
    def save_drawing(self):
        if not self.drawn_cells:
            messagebox.showwarning("Warning", "No drawing to save!")
            return
        
        coordinates = list(self.drawn_cells)
        coordinates.sort()
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(coordinates, f, indent=2)
                messagebox.showinfo("Success", f"Drawing saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = DrawingGrid()
    app.run()