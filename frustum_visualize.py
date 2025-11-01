"""
Frustum Visualization Script

This script visualizes object frustums in 3D space by processing native 6DOF (6 Degrees of Freedom) 
data from Unreal Engine. It generates a sequence of frustum images that represent the rendering 
pipeline effect.

This script is CPU-only and extremely lightweight - no GPU required.

Input: JSON file containing camera and object pose data in UE's native coordinate system
Output: Sequence of PNG images showing frustums with depth-based coloring

Coordinate System Conversion:
- UE Left-Handed: X-Forward, Y-Right, Z-Up
- PyVista Right-Handed: X-Right, Y-Up, Z-Backward
"""

import json
import numpy as np
import pyvista as pv
import math
from pathlib import Path

# ===== Configuration Section =====
INPUT_JSON = r"D:\ue5\projects\first\Saved\Screenshots\Courtyard_Scene\Wooden_Toy_Horse\sine_wave\frustum_data.json"
OUTPUT_DIR = r"D:\ue5\projects\first\Saved\Screenshots\Courtyard_Scene\Wooden_Toy_Horse\sine_wave\output"

FRUSTUM_SCALE = 2                # Overall frustum scale multiplier
FRUSTUM_LENGTH = 100.0             # Frustum length base value (UE units, centimeters)
FRUSTUM_RADIUS = 40.0              # Frustum base radius (UE units, centimeters)
IMAGE_WIDTH = 720                  # Output image width
IMAGE_HEIGHT = 480                 # Output image height
FRAME_DIGITS = 4                   # Frame number zero-padding digits
# ==========================================


# ===== Coordinate Conversion Functions =====
def convert_vector(vec_ue):
    """
    Convert UE left-handed vector to PyVista right-handed vector
    UE (LH): X-Forward, Y-Right, Z-Up
    PyVista (RH): X-Right, Y-Up, Z-Backward
    
    Conversion rule: (x, y, z)_UE -> (y, z, -x)_PV
    """
    x, y, z = vec_ue
    return np.array([y, z, -x])


def convert_rotation_quaternion(q_ue):
    """
    Convert UE left-handed quaternion to PyVista right-handed quaternion
    
    Input: (w, x, y, z)_UE
    Output: (w, y, z, -x)_PV
    """
    w, x, y, z = q_ue
    return np.array([w, y, z, -x])


# ===== Rotation Related Functions =====
def auto_detect_and_convert_euler(roll, pitch, yaw):
    """
    Auto-detect Euler angle units and convert to radians
    
    If any angle's absolute value > 6.28 (approx 2π), assume it's in degrees
    """
    if abs(roll) > 6.28 or abs(pitch) > 6.28 or abs(yaw) > 6.28:
        # Convert to radians
        roll = math.radians(roll)
        pitch = math.radians(pitch)
        yaw = math.radians(yaw)
    return roll, pitch, yaw


def euler_to_rotation_matrix(roll, pitch, yaw):
    """
    Build rotation matrix from Euler angles (UE left-handed system)
    
    Rotation order: Intrinsic ZYX = Extrinsic XYZ
    Matrix multiplication: R = Rx(Roll) * Ry(Pitch) * Rz(Yaw)
    
    Input: Euler angles (radians)
    Output: 3x3 rotation matrix
    """
    # Rx(roll) - Rotation around X-axis
    Rx = np.array([
        [1, 0, 0],
        [0, math.cos(roll), -math.sin(roll)],
        [0, math.sin(roll), math.cos(roll)]
    ])
    
    # Ry(pitch) - Rotation around Y-axis
    Ry = np.array([
        [math.cos(pitch), 0, math.sin(pitch)],
        [0, 1, 0],
        [-math.sin(pitch), 0, math.cos(pitch)]
    ])
    
    # Rz(yaw) - Rotation around Z-axis
    Rz = np.array([
        [math.cos(yaw), -math.sin(yaw), 0],
        [math.sin(yaw), math.cos(yaw), 0],
        [0, 0, 1]
    ])
    
    # Combine: R = Rx * Ry * Rz
    R = Rx @ Ry @ Rz
    return R


# ===== Frustum Geometry Functions =====
def create_frustum_vertices_model_space():
    """
    Create pyramid frustum vertices (model space, UE left-handed system)
    
    Aligned with infer_depth_grey_mesh.py shape
    
    Geometric center at (0,0,0)
    Apex points along +X axis (Forward direction)
    
    Output: 5x3 numpy array
    """
    L = FRUSTUM_LENGTH  # Frustum length
    aspect_ratio = IMAGE_WIDTH / IMAGE_HEIGHT  # Aspect ratio 1.5
    H = FRUSTUM_RADIUS * 2  # Base height
    W = H * aspect_ratio     # Base width
    
    vertices = np.array([
        # v0: Apex (camera position)
        [0.0, 0.0, 0.0],
        
        # v1-v4: Four base corners (on X=L plane)
        [L,  W/2,  H/2],   # v1: Top-right
        [L,  W/2, -H/2],   # v2: Bottom-right
        [L, -W/2, -H/2],   # v3: Bottom-left
        [L, -W/2,  H/2],   # v4: Top-left
    ])
    
    return vertices


def create_frustum_faces():
    """
    Create pyramid faces (4 triangular side faces)
    
    Aligned with infer_depth_grey_mesh.py structure
    
    PyVista format: [3, v0, v1, v2, 3, v3, v4, v5, ...]
    """
    faces = [
        # Four triangular side faces (from apex v0 to edges)
        3, 0, 1, 2,  # Right side
        3, 0, 2, 3,  # Bottom side
        3, 0, 3, 4,  # Left side
        3, 0, 4, 1,  # Top side
    ]
    
    return faces


def transform_frustum_to_world(vertices_model, position_ue, rotation_ue, scale):
    """
    Transform frustum from model space to world space (UE left-handed system)
    
    Input:
        vertices_model: Model space vertices (5x3)
        position_ue: Object world position [x, y, z]
        rotation_ue: Object rotation Euler angles [roll, pitch, yaw]
        scale: Scale multiplier
    
    Output:
        World space vertices (5x3, UE left-handed system)
    """
    # 1. Scale
    vertices_scaled = vertices_model * scale
    
    # 2. Rotate
    roll, pitch, yaw = auto_detect_and_convert_euler(*rotation_ue)
    R = euler_to_rotation_matrix(roll, pitch, yaw)
    vertices_rotated = (R @ vertices_scaled.T).T  # (3x3) @ (3x5) = (3x5), transpose back to (5x3)
    
    # 3. Translate
    vertices_world = vertices_rotated + np.array(position_ue)
    
    return vertices_world


def convert_vertices_to_pyvista(vertices_world_ue):
    """
    Convert world space vertices from UE left-handed to PyVista right-handed system
    
    Input: Vertex array (Nx3, UE left-handed)
    Output: Vertex array (Nx3, PyVista right-handed)
    """
    vertices_pv = np.array([convert_vector(v) for v in vertices_world_ue])
    return vertices_pv


# ===== Depth and Color Computation Functions =====
def compute_projection_depth(obj_pos_pv, cam_pos_pv, cam_forward_pv):
    """
    Compute object's projection depth (along camera Forward direction)
    
    Input:
        obj_pos_pv: Object position (PyVista right-handed)
        cam_pos_pv: Camera position (PyVista right-handed)
        cam_forward_pv: Camera Forward vector (PyVista right-handed, normalized)
    
    Output:
        Projection depth (scalar)
    """
    vec_cam_to_obj = obj_pos_pv - cam_pos_pv
    depth = np.dot(vec_cam_to_obj, cam_forward_pv)
    return depth


def depth_to_color(depth, near_clip, far_clip):
    """
    Map depth value to grayscale color (near = light, far = dark)
    
    Reference infer_depth_grey_mesh.py grayscale mapping logic:
    - Near (small depth): Light gray (0.92)
    - Far (large depth): Dark gray (0.25)
    
    Input:
        depth: Projection depth
        near_clip: Near clipping plane distance
        far_clip: Far clipping plane distance
    
    Output:
        RGB color [r, g, b], range [0, 1]
    """
    # Normalize to [0, 1]
    t = (depth - near_clip) / (far_clip - near_clip)
    t = np.clip(t, 0.0, 1.0)
    
    # Grayscale brightness range: near = brighter, far = darker
    light_hi = 0.92   # Near brightness (close to white)
    light_lo = 0.25   # Far brightness (dark gray)
    
    # Calculate grayscale value: t=0(near)→light_hi(bright), t=1(far)→light_lo(dark)
    light = light_hi * (1.0 - t) + light_lo * t
    
    # Return grayscale RGB (R=G=B)
    return np.array([light, light, light])


# ===== Camera Setup Functions =====
def setup_camera(plotter, cam_data, use_original_clipping=False):
    """
    Set PyVista camera parameters
    
    Input:
        plotter: PyVista Plotter object
        cam_data: Camera data dictionary containing:
            - position: Camera position [x, y, z] (UE left-handed)
            - rotation: Camera rotation [roll, pitch, yaw] (UE left-handed)
            - fov_vertical: Vertical FOV (degrees)
            - near_clip, far_clip: Clipping plane distances
        use_original_clipping: Whether to use original clipping_range (not depth range)
    
    Output:
        cam_pos_pv: Camera position (PyVista right-handed)
        cam_forward_pv: Camera Forward vector (PyVista right-handed, normalized)
    """
    # 1. Convert camera position
    position_ue = cam_data['position']
    cam_pos_pv = convert_vector(position_ue)
    
    # 2. Calculate camera Forward vector from Euler angles
    rotation_ue = cam_data['rotation']
    roll, pitch, yaw = auto_detect_and_convert_euler(*rotation_ue)
    R_cam_ue = euler_to_rotation_matrix(roll, pitch, yaw)
    
    # In UE, Forward is +X axis
    forward_ue = R_cam_ue @ np.array([1, 0, 0])
    
    # 3. Convert Forward vector to PyVista coordinate system
    cam_forward_pv = convert_vector(forward_ue)
    cam_forward_pv = cam_forward_pv / np.linalg.norm(cam_forward_pv)  # Normalize
    
    # 4. Calculate FocalPoint
    focal_point_pv = cam_pos_pv + cam_forward_pv * 1.0
    
    # 5. Calculate ViewUp vector (UE's Z-Up converted to PyVista)
    view_up_ue = np.array([0, 0, 1])  # UE's Z-Up
    view_up_pv = convert_vector(view_up_ue)
    view_up_pv = view_up_pv / np.linalg.norm(view_up_pv)  # Normalize
    
    # 6. Set camera parameters
    plotter.camera.position = cam_pos_pv
    plotter.camera.focal_point = focal_point_pv
    plotter.camera.up = view_up_pv
    plotter.camera.view_angle = cam_data['fov_vertical']
    
    # 7. Handle clipping_range
    if use_original_clipping:
        # Use original configured clipping range (for rendering, ensure frustum not clipped)
        plotter.camera.clipping_range = (10.0, 10000.0)
    else:
        # Use depth range (only for color mapping, doesn't affect clipping)
        pass  # Don't set clipping_range
    
    return cam_pos_pv, cam_forward_pv


# ===== Data Loading Functions =====
def load_json_data(filepath):
    """
    Load and parse JSON data file
    
    Input: JSON file path
    Output: Parsed dictionary
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


# ===== Main Function =====
def main():
    """
    Main function: Load data and render all frames
    """
    print("\n" + "="*60)
    print("Frustum Visualization Rendering Started")
    print("="*60)
    
    # 1. Create output directory
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {output_dir.absolute()}")
    
    # 2. Load JSON data
    print(f"Loading data file: {INPUT_JSON}")
    data = load_json_data(INPUT_JSON)
    
    # 3. Extract camera data and frame list
    cam_data = data['camera']
    frames = data['frames']
    
    print(f"Camera position: {cam_data['position']}")
    print(f"Camera rotation: {cam_data['rotation']}")
    print(f"FOV: {cam_data['fov_vertical']}°")
    print(f"Total frames: {len(frames)}")
    
    # ===== First pass: Calculate actual depth range (for color mapping only) =====
    print(f"\nScanning depth range...")
    
    # Calculate camera position and Forward vector (no plotter needed)
    position_ue = cam_data['position']
    cam_pos_pv = convert_vector(position_ue)
    
    rotation_ue = cam_data['rotation']
    roll, pitch, yaw = auto_detect_and_convert_euler(*rotation_ue)
    R_cam_ue = euler_to_rotation_matrix(roll, pitch, yaw)
    forward_ue = R_cam_ue @ np.array([1, 0, 0])
    cam_forward_pv = convert_vector(forward_ue)
    cam_forward_pv = cam_forward_pv / np.linalg.norm(cam_forward_pv)
    
    # Calculate depth for all frames
    depths = []
    for frame_data in frames:
        obj_position_ue = frame_data['object']['position']
        obj_pos_pv = convert_vector(obj_position_ue)
        depth = compute_projection_depth(obj_pos_pv, cam_pos_pv, cam_forward_pv)
        depths.append(depth)
    
    depths = np.array(depths)
    depth_min = depths.min()
    depth_max = depths.max()
    
    print(f"Depth range: [{depth_min:.2f}, {depth_max:.2f}]")
    
    # Save depth range to independent variable (don't modify cam_data's clipping_range)
    color_depth_range = (depth_min, depth_max)
    # ==========================================
    
    # 4. Loop render each frame
    print(f"\nStarting render...")
    for i, frame_data in enumerate(frames):
        frame_id = frame_data['frame_id']
        
        # Pass color depth range
        output_path = render_frame(frame_data, cam_data, frame_id, color_depth_range)
        
        # Print progress
        progress = (i + 1) / len(frames) * 100
        print(f"  [{i+1}/{len(frames)}] ({progress:.1f}%) - Frame {frame_id} -> {output_path.name}")
    
    # 5. Complete
    print("\n" + "="*60)
    print(f"Rendering complete! Generated {len(frames)} images")
    print(f"Output directory: {output_dir.absolute()}")
    print("="*60 + "\n")


# ===== Main Rendering Function =====
def render_frame(frame_data, cam_data, frame_id, color_depth_range):
    """
    Render single frame image
    
    Input:
        frame_data: Current frame's object data (position, rotation)
        cam_data: Camera data
        frame_id: Frame number
        color_depth_range: (depth_min, depth_max) for color mapping
    
    Output:
        Saved image file path
    """
    # 1. Create PyVista Plotter (off-screen rendering)
    plotter = pv.Plotter(off_screen=True, window_size=[IMAGE_WIDTH, IMAGE_HEIGHT])
    plotter.set_background('black')
    
    # 2. Setup camera (using original wide-range clipping_range)
    cam_pos_pv, cam_forward_pv = setup_camera(plotter, cam_data, use_original_clipping=True)
    
    # 3. Get object position and rotation (UE left-handed)
    obj_position_ue = frame_data['object']['position']
    obj_rotation_ue = frame_data['object']['rotation']
    
    # 4. Convert object position to PyVista coordinate system
    obj_pos_pv = convert_vector(obj_position_ue)
    
    # 5. Calculate projection depth
    depth = compute_projection_depth(obj_pos_pv, cam_pos_pv, cam_forward_pv)
    
    # 6. Calculate grayscale color (using independent depth range)
    depth_min, depth_max = color_depth_range
    color = depth_to_color(depth, depth_min, depth_max)
    
    # 7. Create frustum vertices (model space)
    vertices_model = create_frustum_vertices_model_space()
    
    # 8. Transform frustum to world space (UE left-handed)
    vertices_world_ue = transform_frustum_to_world(
        vertices_model,
        obj_position_ue,
        obj_rotation_ue,
        FRUSTUM_SCALE
    )
    
    # 9. Convert frustum vertices to PyVista coordinate system
    vertices_world_pv = convert_vertices_to_pyvista(vertices_world_ue)
    
    # 10. Create PyVista PolyData mesh
    faces = create_frustum_faces()
    mesh = pv.PolyData(vertices_world_pv, faces)
    
    # 11. Add mesh to scene: grayscale fill + red edge lines + semi-transparent
    plotter.add_mesh(
        mesh, 
        color=color,           # Grayscale fill color
        opacity=0.85,          # Semi-transparent (0~1, 0=fully transparent, 1=fully opaque)
        show_edges=True,       # Show edges
        edge_color='red',      # Edge line color changed to red
        line_width=2           # Edge line width
    )
    
    # 12. Screenshot and save
    output_path = Path(OUTPUT_DIR) / f"frame_{frame_id:0{FRAME_DIGITS}d}.png"
    plotter.screenshot(str(output_path))
    
    # 13. Close plotter
    plotter.close()
    
    return output_path


# ===== Program Entry Point =====
if __name__ == "__main__":
    main()