import matplotlib.pyplot as plt
import numpy as np

# 1. Define plot setup function
def setup_plot():
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_facecolor('#F5F5F5')  # Set light gray background
    
    # Manually draw grid lines
    grid_spacing = 2  # Draw a grid line every 2 units
    for x in range(-12, 13, grid_spacing):
        ax.axvline(x, color='#CCCCCC', linewidth=0.8, alpha=0.6, zorder=0)
    for y in range(-12, 13, grid_spacing):
        ax.axhline(y, color='#CCCCCC', linewidth=0.8, alpha=0.6, zorder=0)
    
    # Draw main axes
    ax.axhline(0, color='#E84A5F', linewidth=1.5, zorder=1)  # Red X-axis
    ax.axvline(0, color='#4CAF50', linewidth=1.5, zorder=1)  # Green Y-axis
    
    ax.set_aspect('equal', adjustable='box')  # Keep aspect ratio equal
    ax.set_xlim(-12, 12)  # Fix X-axis range
    ax.set_ylim(-12, 12)  # Fix Y-axis range
    ax.set_title("Parametric Curves (Two Objs)", color='#333333')
    
    return ax

# 2. Generate data
t = np.linspace(0, 1.8 * np.pi, 300)  # Shorter trajectory with fewer points

# Trajectory 1 (Upper-right quadrant - simplified)
x1 = 6 * np.sin(t) * (1 + 0.15 * np.sin(1.5*t)) + 3
y1 = 5 * np.cos(t) * (1 + 0.1 * np.cos(1.2*t)) + 3

# Trajectory 2 (Lower-left quadrant - smoother)
x2 = 5.5 * np.sin(t + 0.3) * (1 + 0.2 * np.sin(1.8*t)) - 3
y2 = 4.5 * np.cos(0.9*t) * (1 + 0.15 * np.cos(1.5*t)) - 2.5

# 3. Plot
ax = setup_plot()
ax.plot(x1, y1, color='#333333', linewidth=1.5, zorder=2)  # Dark gray line
ax.plot(x2, y2, color='#333333', linewidth=1.5, zorder=2)

# Hide axis ticks
ax.set_xticks([])
ax.set_yticks([])

plt.show()
