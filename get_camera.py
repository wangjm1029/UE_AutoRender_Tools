"""
Camera 6DOF Data Query Script

This script provides a convenient way to retrieve the current editor viewport camera's 
6DOF (6 Degrees of Freedom) data including position (x, y, z) and rotation (roll, pitch, yaw).
Use this to quickly check camera parameters for configuration in the main rendering script.
"""

import unreal

# Get editor subsystem
editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

# get_level_viewport_camera_info() returns a tuple that needs unpacking
camera_info = editor_subsystem.get_level_viewport_camera_info()

# Tuple contains two elements: location and rotation
camera_location = camera_info[0]  # First element is location
camera_rotation = camera_info[1]  # Second element is rotation

print(f"Camera Location: {camera_location}")
print(f"Camera Rotation: {camera_rotation}")

