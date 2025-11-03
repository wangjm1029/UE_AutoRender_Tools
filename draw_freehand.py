"""
Interactive Trajectory Drawing Tool 
Description: Draw parametric curves with mouse, like drawing in Word
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button
from scipy.interpolate import splprep, splev
from typing import List, Optional, Tuple


class TrajectoryCanvas:
    """Main canvas for drawing trajectories"""
    
    def __init__(self, figsize: Tuple[int, int] = (10, 10)):
        """
        Initialize the drawing canvas
        
        Args:
            figsize: Figure size as (width, height) tuple
        """
        self.fig, self.ax = plt.subplots(figsize=figsize)
        plt.subplots_adjust(left=0.1, bottom=0.12, right=0.9, top=0.95)
        
        # Canvas settings
        self.xlim = (-12, 12)
        self.ylim = (-12, 12)
        self.background_color = '#F5F5F5'
        self.grid_color = '#CCCCCC'
        self.axis_x_color = '#E84A5F'  # Red
        self.axis_y_color = '#4CAF50'  # Green
        
        self._setup_canvas()
    
    def _setup_canvas(self):
        """Setup the canvas with grid and axes"""
        self.ax.clear()
        self.ax.set_facecolor(self.background_color)
        
        # Draw grid lines
        grid_spacing = 2
        for x in range(self.xlim[0], self.xlim[1] + 1, grid_spacing):
            self.ax.axvline(x, color=self.grid_color, linewidth=0.8, alpha=0.6, zorder=0)
        for y in range(self.ylim[0], self.ylim[1] + 1, grid_spacing):
            self.ax.axhline(y, color=self.grid_color, linewidth=0.8, alpha=0.6, zorder=0)
        
        # Draw coordinate axes
        self.ax.axhline(0, color=self.axis_x_color, linewidth=1.5, zorder=1)
        self.ax.axvline(0, color=self.axis_y_color, linewidth=1.5, zorder=1)
        
        # Set limits and appearance
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.set_xlim(self.xlim)
        self.ax.set_ylim(self.ylim)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
    
    def update_title(self, num_curves: int):
        """
        Update canvas title based on number of curves
        
        Args:
            num_curves: Number of curves currently drawn
        """
        if num_curves == 0:
            title = "Draw Your Trajectories - Click and Drag to Draw"
        elif num_curves == 1:
            title = "Parametric Curve (Single Obj)"
        elif num_curves == 2:
            title = "Parametric Curves (Two Objs)"
        else:
            title = "Parametric Curves (Three Objs)"
        
        self.ax.set_title(title, color='#333333', fontsize=14)
    
    def redraw(self):
        """Refresh the canvas"""
        self.fig.canvas.draw_idle()


class Curve:
    """Represents a single drawn curve"""
    
    def __init__(self, points: List[List[float]], smoothness: float = 0.5):
        """
        Initialize a curve with raw points
        
        Args:
            points: List of [x, y] coordinates
            smoothness: Smoothing factor for spline interpolation
        """
        self.raw_points = np.array(points)
        self.smoothed_points = self._smooth_curve(smoothness)
        self.color = '#333333'
        self.linewidth = 1.5
    
    def _smooth_curve(self, smoothness: float) -> np.ndarray:
        """
        Apply spline interpolation to smooth the curve
        
        Args:
            smoothness: Smoothing parameter (higher = smoother)
        
        Returns:
            Smoothed points as numpy array
        """
        if len(self.raw_points) < 4:
            return self.raw_points
        
        x = self.raw_points[:, 0]
        y = self.raw_points[:, 1]
        
        try:
            # B-spline interpolation
            tck, u = splprep([x, y], 
                           s=smoothness * len(self.raw_points),  # Adaptive smoothing
                           k=min(3, len(self.raw_points) - 1))   # Cubic spline
            
            # Resample with 3x points for smoothness
            u_new = np.linspace(0, 1, len(self.raw_points) * 3)
            x_smooth, y_smooth = splev(u_new, tck)
            
            return np.column_stack([x_smooth, y_smooth])
        
        except Exception as e:
            print(f"Smoothing failed: {e}, using raw points")
            return self.raw_points
    
    def plot(self, ax, **kwargs):
        """
        Plot this curve on given axes
        
        Args:
            ax: Matplotlib axes to plot on
            **kwargs: Additional plot parameters
        """
        plot_params = {
            'color': self.color,
            'linewidth': self.linewidth,
            'zorder': 2
        }
        plot_params.update(kwargs)
        
        ax.plot(self.smoothed_points[:, 0], 
               self.smoothed_points[:, 1], 
               **plot_params)
    
    def export_data(self) -> str:
        """
        Export curve data as formatted string
        
        Returns:
            Formatted coordinate string
        """
        lines = []
        for point in self.smoothed_points:
            lines.append(f"{point[0]:.4f}, {point[1]:.4f}")
        return "\n".join(lines)


class DrawingManager:
    """Manages the drawing state and curve collection"""
    
    MAX_CURVES = 3
    MIN_POINTS = 10  # Minimum points to save a curve
    
    def __init__(self, canvas: TrajectoryCanvas):
        """
        Initialize drawing manager
        
        Args:
            canvas: The canvas to draw on
        """
        self.canvas = canvas
        self.curves: List[Curve] = []
        
        # Drawing state
        self.is_drawing = False
        self.current_points: List[List[float]] = []
        self.current_line = None  # Line2D object for preview
        
        # Preview line style
        self.preview_color = '#FF6B6B'
        self.preview_linewidth = 2
        self.preview_alpha = 0.7
    
    def start_drawing(self, x: float, y: float):
        """
        Start a new curve
        
        Args:
            x, y: Starting coordinates
        """
        if len(self.curves) >= self.MAX_CURVES:
            self.canvas.ax.set_title(
                f"Maximum {self.MAX_CURVES} curves reached! Clear to draw more.",
                color='red', fontsize=14
            )
            self.canvas.redraw()
            return
        
        self.is_drawing = True
        self.current_points = [[x, y]]
        
        # Create preview line
        self.current_line, = self.canvas.ax.plot(
            [x], [y],
            color=self.preview_color,
            linewidth=self.preview_linewidth,
            zorder=3,
            alpha=self.preview_alpha
        )
        self.canvas.redraw()
    
    def continue_drawing(self, x: float, y: float):
        """
        Add point to current curve
        
        Args:
            x, y: New point coordinates
        """
        if not self.is_drawing:
            return
        
        self.current_points.append([x, y])
        
        # Update preview line
        if len(self.current_points) > 1 and self.current_line:
            points = np.array(self.current_points)
            self.current_line.set_data(points[:, 0], points[:, 1])
            self.canvas.redraw()
    
    def finish_drawing(self):
        """Finish current curve and save if valid"""
        if not self.is_drawing:
            return
        
        self.is_drawing = False
        
        # Only save if curve has enough points
        if len(self.current_points) > self.MIN_POINTS:
            curve = Curve(self.current_points, smoothness=0.5)
            self.curves.append(curve)
        
        # Clean up
        self.current_points = []
        self.current_line = None
        self.redraw_all()
    
    def undo_last(self):
        """Remove the last drawn curve"""
        if self.curves:
            self.curves.pop()
            self.redraw_all()
    
    def clear_all(self):
        """Remove all curves"""
        self.curves.clear()
        self.redraw_all()
    
    def redraw_all(self):
        """Redraw all curves on canvas"""
        self.canvas._setup_canvas()
        self.canvas.update_title(len(self.curves))
        
        for curve in self.curves:
            curve.plot(self.canvas.ax)
        
        self.canvas.redraw()
    
    def export_to_file(self, filename: str = 'trajectory_data.txt'):
        """
        Export all curves to text file
        
        Args:
            filename: Output filename
        """
        if not self.curves:
            print("No curves to export!")
            return
        
        with open(filename, 'w') as f:
            for i, curve in enumerate(self.curves):
                f.write(f"# Curve {i + 1}\n")
                f.write(curve.export_data())
                f.write("\n\n")
        
        print(f"Exported {len(self.curves)} curves to {filename}")
    
    def save_image(self, filename: Optional[str] = None):
        """
        Save canvas as PNG image
        
        Args:
            filename: Output filename (auto-generated if None)
        """
        if not self.curves:
            print("No curves to save!")
            return
        
        if filename is None:
            filename = f'curves_{len(self.curves)}obj_drawn.png'
        
        self.canvas.fig.savefig(
            filename,
            dpi=300,
            bbox_inches='tight',
            facecolor='white'
        )
        print(f'Saved as {filename}')


class UIController:
    """Controls UI buttons and user interactions"""
    
    def __init__(self, drawing_manager: DrawingManager):
        """
        Initialize UI controller
        
        Args:
            drawing_manager: The drawing manager to control
        """
        self.manager = drawing_manager
        self.canvas = drawing_manager.canvas
        self.buttons = {}
        
        self._create_buttons()
        self._connect_events()
    
    def _create_buttons(self):
        """Create all UI buttons"""
        button_configs = [
            ('clear', [0.15, 0.02, 0.12, 0.05], 'Clear All', 'lightcoral', 'red'),
            ('undo', [0.3, 0.02, 0.12, 0.05], 'Undo Last', 'lightyellow', 'yellow'),
            ('export', [0.45, 0.02, 0.12, 0.05], 'Export Data', 'lightblue', 'skyblue'),
            ('save', [0.6, 0.02, 0.12, 0.05], 'Save PNG', 'lightgreen', 'green'),
            ('help', [0.75, 0.02, 0.12, 0.05], 'Help', 'lightgray', 'gray'),
        ]
        
        for name, pos, label, color, hovercolor in button_configs:
            ax_button = plt.axes(pos)
            button = Button(ax_button, label, color=color, hovercolor=hovercolor)
            self.buttons[name] = button
        
        # Connect button callbacks
        self.buttons['clear'].on_clicked(lambda e: self.manager.clear_all())
        self.buttons['undo'].on_clicked(lambda e: self.manager.undo_last())
        self.buttons['export'].on_clicked(lambda e: self.manager.export_to_file())
        self.buttons['save'].on_clicked(lambda e: self.manager.save_image())
        self.buttons['help'].on_clicked(lambda e: self._show_help())
    
    def _connect_events(self):
        """Connect mouse events to drawing manager"""
        fig = self.canvas.fig
        
        fig.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        fig.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
        fig.canvas.mpl_connect('button_release_event', self._on_mouse_release)
    
    def _on_mouse_press(self, event):
        """Handle mouse press event"""
        if event.inaxes != self.canvas.ax:
            return
        self.manager.start_drawing(event.xdata, event.ydata)
    
    def _on_mouse_move(self, event):
        """Handle mouse move event"""
        if event.inaxes != self.canvas.ax:
            return
        self.manager.continue_drawing(event.xdata, event.ydata)
    
    def _on_mouse_release(self, event):
        """Handle mouse release event"""
        self.manager.finish_drawing()
    
    def _show_help(self):
        """Display help information"""
        help_text = """
╔════════════════════════════════════════╗
║         HOW TO USE                     ║
╠════════════════════════════════════════╣
║ 1. Click and drag to draw a curve     ║
║ 2. Release to finish the curve        ║
║ 3. Draw up to 3 curves                ║
║ 4. Use buttons:                        ║
║    • Undo Last: Remove last curve     ║
║    • Clear All: Remove all curves     ║
║    • Export Data: Save coordinates    ║
║    • Save PNG: Save image             ║
╚════════════════════════════════════════╝
"""
        print(help_text)


class TrajectoryDrawingApp:
    """Main application class - orchestrates all components"""
    
    def __init__(self):
        """Initialize the application"""
        # Create components
        self.canvas = TrajectoryCanvas(figsize=(10, 10))
        self.drawing_manager = DrawingManager(self.canvas)
        self.ui_controller = UIController(self.drawing_manager)
        
        # Initial setup
        self.canvas.update_title(0)
    
    def run(self):
        """Start the application"""
        print(" Trajectory Drawing Tool Started!")
        print("Click and drag to draw curves...")
        plt.show()


# ============ Entry Point ============
if __name__ == '__main__':
    app = TrajectoryDrawingApp()
    app.run()
