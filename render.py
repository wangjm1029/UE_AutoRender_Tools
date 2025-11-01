"""
Comprehensive Rendering System for Unreal Engine 5.1
===================================================
This script automates batch rendering of multiple assets with various motion patterns
across different HDRI environments in Unreal Engine.

Architecture: HDRI Scenes × Assets × Motion Patterns
Rendering Order: HDRI1 -> Asset1 -> Motion1, Motion2... -> Asset2 -> Motion1... -> HDRI2 -> ...
"""

import unreal
import os
import sys
import math
import json


# Path configuration for module imports
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.append(script_dir)
except NameError:
    unreal.log_warning("Unable to determine script path automatically, relying on UE default path settings.")

# Import custom utility modules
from utils.asset_utils import spawn_static_mesh_actor
from utils.level_utils import load_map
from motion_patterns import get_position_for_motion


class AnimationRenderer:
    """
    Single Animation Renderer
    =========================
    Handles rendering of a single asset with one motion pattern, capturing screenshots
    and collecting motion data (position, rotation, displacement) for each frame.
    
    Supported Motion Types:
    - sine_wave: Forward movement with sinusoidal Y-axis oscillation
    - z_shape: Three-segment Z-shaped trajectory
    - circle: Circular motion while advancing along X-axis
    - spiral: Spiral motion with expanding radius
    - square_wave: Square wave Y-axis pattern
    - linear: Straight-line motion (default)
    """
    
    def __init__(self, actor_label, output_dir, on_finished_callback, num_frames=5,
                 total_distance=500.0, total_rotation=360.0, y_amplitude=100.0,
                 y_frequency=2.0, motion_type="sine_wave", prune_last_frame=True, **kwargs):
        """
        Initialize animation renderer
        
        Args:
            actor_label: Target actor's label name
            output_dir: Output directory for screenshots and JSON data
            on_finished_callback: Callback function when rendering completes
            num_frames: Total number of frames to render
            total_distance: Total distance to move along X-axis
            total_rotation: Total rotation angle (yaw axis)
            y_amplitude: Amplitude of Y-axis motion
            y_frequency: Frequency of oscillation
            motion_type: Type of motion pattern
        """
        self.actor_label = actor_label
        self.output_dir = output_dir
        self.on_finished_callback = on_finished_callback
        self.num_frames = num_frames                # Original frame count (including last frame to be discarded)
        self.prune_last_frame = prune_last_frame    # Whether to discard the last frame
        self.total_distance = total_distance
        self.total_rotation = total_rotation
        self.y_amplitude = y_amplitude
        self.y_frequency = y_frequency
        self.motion_type = motion_type
        self.target_scale = kwargs.get("target_scale", {"x": 1.0, "y": 1.0, "z": 1.0})
        
        # Metadata from kwargs
        self.asset_path = kwargs.get("asset_path", "")
        self.hdri_name = kwargs.get("hdri_name", "")
        self.hdri_path = kwargs.get("hdri_path", "")
        self.camera_config = kwargs.get("camera_config", {})
        
        self.frame_index = 0
        self.target_actor = None
        self.start_position = None
        self.start_rotation = None
        self.callback_handle = None
        self.previous_position = None
        self.frame_data = []

        # Additional state for deleting the last frame
        self._delete_attempts = 0
        self._delete_callback = None
        self.last_frame_path = None

    def start(self):
        """Initialize and start the rendering process"""
        self._cleanup_callback()
        
        # Find target actor by label
        editor_actor_subs = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        all_actors = editor_actor_subs.get_all_level_actors()
        found_actors = [actor for actor in all_actors if actor.get_actor_label() == self.actor_label]
        
        if not found_actors:
            unreal.log_error(f"Target actor '{self.actor_label}' not found!")
            if self.on_finished_callback: 
                self.on_finished_callback()
            return
            
        self.target_actor = found_actors[0]
        
        # Apply scale
        scale_vec = unreal.Vector(self.target_scale["x"], self.target_scale["y"], self.target_scale["z"])
        self.target_actor.set_actor_scale3d(scale_vec)
        
        # Record initial state
        self.start_position = self.target_actor.get_actor_location()
        self.start_rotation = self.target_actor.get_actor_rotation()
        self.previous_position = self.start_position
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Start animation
        self._move_actor_and_schedule_screenshot()


    def _move_actor_and_schedule_screenshot(self):
        """Calculate and apply motion for current frame, then schedule screenshot"""
        alpha = self.frame_index / (self.num_frames - 1) if self.num_frames > 1 else 0.0
        
        # Build motion parameters
        motion_params = {
            'total_distance': self.total_distance,
            'y_amplitude': self.y_amplitude,
            'y_frequency': self.y_frequency
        }
        
        # Calculate position using motion patterns module
        current_x, current_y, current_z = get_position_for_motion(
            self.motion_type,
            alpha,
            self.start_position.x,
            self.start_position.y,
            self.start_position.z,
            self.frame_index,
            self.num_frames,
            motion_params
        )
        
        current_position = unreal.Vector(current_x, current_y, current_z)
        self.target_actor.set_actor_location(current_position, False, True)

        current_yaw = self.start_rotation.yaw + alpha * self.total_rotation
        current_rotation = unreal.Rotator(
            pitch=self.start_rotation.pitch,
            yaw=current_yaw,
            roll=self.start_rotation.roll
        )
        self.target_actor.set_actor_rotation(current_rotation, True)

        self.callback_handle = unreal.register_slate_post_tick_callback(self._take_screenshot_and_collect_data)


    def _take_screenshot_and_collect_data(self, _):
        """Capture screenshot and collect motion data for current frame"""
        self._cleanup_callback()
        current_location = self.target_actor.get_actor_location()
        current_rotation = self.target_actor.get_actor_rotation()
        displacement = current_location - self.previous_position

        # Only export raw UE data - no conversion needed
        # infer.py will handle all coordinate transformations
        data_entry = {
            "frame_index": self.frame_index,
            "timestamp": self.frame_index / max(1, self.num_frames - 1),
            "pose": {
                "translation": {"x": current_location.x, "y": current_location.y, "z": current_location.z},
                "euler_angles": {
                    "pitch": current_rotation.pitch,
                    "yaw": current_rotation.yaw,
                    "roll": current_rotation.roll
                }
            },
            "motion": {
                "displacement": {"x": displacement.x, "y": displacement.y, "z": displacement.z},
                "displacement_magnitude": math.sqrt(displacement.x**2 + displacement.y**2 + displacement.z**2)
            },
            "image_filename": f"frame_{self.frame_index:04d}.png"
        }
        self.frame_data.append(data_entry)
        self.previous_position = current_location

        screenshot_path = os.path.join(self.output_dir, f"frame_{self.frame_index:04d}.png")
        unreal.AutomationLibrary.take_high_res_screenshot(720, 480, screenshot_path)

        self.frame_index += 1
        if self.frame_index < self.num_frames:
            self._move_actor_and_schedule_screenshot()
        else:
            # Changed to asynchronously delete last frame then export
            self._finalize_and_prune()

    def _finalize_and_prune(self):
        """
        Process after the last frame:
        1. Remove last frame data from frame_data (keep JSON without this frame)
        2. Poll and wait for screenshot file to be written to disk, then delete
        3. Export JSON after successful deletion or timeout
        """
        if self.prune_last_frame and len(self.frame_data) > 1:
            pruned_entry = self.frame_data.pop()  # Remove last frame data
            last_filename = pruned_entry["image_filename"]
            self.last_frame_path = os.path.join(self.output_dir, last_filename)
            unreal.log(f"Scheduling prune of last frame file: {self.last_frame_path}")
            self._schedule_delete_last_frame()
        else:
            self._export_frame_data_to_json()
            if self.on_finished_callback:
                self.on_finished_callback()

    def _schedule_delete_last_frame(self):
        """Register Tick polling, wait for file to appear and then delete"""
        if self._delete_callback:
            unreal.unregister_slate_post_tick_callback(self._delete_callback)

        def _poll(_):
            if not self.last_frame_path:
                unreal.log_warning("Last frame path not set; exporting JSON directly.")
                self._cleanup_delete_callback()
                self._export_frame_data_to_json()
                if self.on_finished_callback:
                    self.on_finished_callback()
                return

            if os.path.exists(self.last_frame_path):
                try:
                    os.remove(self.last_frame_path)
                    unreal.log(f"Pruned last frame image: {self.last_frame_path}")
                except Exception as e:
                    unreal.log_error(f"Failed to delete last frame image: {e}")
                self._cleanup_delete_callback()
                self._export_frame_data_to_json()
                if self.on_finished_callback:
                    self.on_finished_callback()
            else:
                self._delete_attempts += 1
                if self._delete_attempts % 10 == 0:
                    unreal.log(f"Waiting for last frame file to appear (attempt {self._delete_attempts})")
                if self._delete_attempts > 60:  # After ~60 ticks (~1 second+) give up deletion
                    unreal.log_warning(f"Timeout waiting for last frame image: {self.last_frame_path}")
                    self._cleanup_delete_callback()
                    self._export_frame_data_to_json()
                    if self.on_finished_callback:
                        self.on_finished_callback()

        self._delete_callback = unreal.register_slate_post_tick_callback(_poll)

    def _cleanup_delete_callback(self):
        if self._delete_callback:
            unreal.unregister_slate_post_tick_callback(self._delete_callback)
            self._delete_callback = None

    def _export_frame_data_to_json(self):
        """
        Export JSON format required by frustum visualization script
        
        Output file: frustum_data.json
        Format:
        {
        "camera": {
            "position": [x, y, z],          // UE left-handed system, centimeters
            "rotation": [roll, pitch, yaw], // Degrees
            "fov_vertical": 90.0,
            "aspect_ratio": 1.5,
            "near_clip": 10.0,
            "far_clip": 10000.0
        },
        "frames": [
            {
            "frame_id": 0,
            "object": {
                "position": [x, y, z],      // UE left-handed system, centimeters
                "rotation": [roll, pitch, yaw] // Degrees
            }
            }
        ]
        }
        """
        
        frames_to_save = self.frame_data
        
        # ===== Build camera data =====
        cam_loc = self.camera_config.get("location", {})
        cam_rot = self.camera_config.get("rotation", {})
        
        camera_data = {
            "position": [
                cam_loc.get("x", 0.0),
                cam_loc.get("y", 0.0),
                cam_loc.get("z", 0.0)
            ],
            "rotation": [
                cam_rot.get("roll", 0.0),   # UE: X-axis rotation
                cam_rot.get("pitch", 0.0),  # UE: Y-axis rotation
                cam_rot.get("yaw", 0.0)     # UE: Z-axis rotation
            ],
            "fov_vertical": self.camera_config.get("fov", 90.0),
            "aspect_ratio": 720.0 / 480.0,  # Fixed aspect ratio
            "near_clip": 10.0,              # Near clipping plane (centimeters)
            "far_clip": 10000.0             # Far clipping plane (centimeters)
        }
        
        # ===== Build frame data =====
        frames_output = []
        for frame_data in frames_to_save:
            frame_entry = {
                "frame_id": frame_data["frame_index"],
                "object": {
                    "position": [
                        frame_data["pose"]["translation"]["x"],
                        frame_data["pose"]["translation"]["y"],
                        frame_data["pose"]["translation"]["z"]
                    ],
                    "rotation": [
                        frame_data["pose"]["euler_angles"]["roll"],   # UE: X-axis
                        frame_data["pose"]["euler_angles"]["pitch"],  # UE: Y-axis
                        frame_data["pose"]["euler_angles"]["yaw"]     # UE: Z-axis
                    ]
                }
            }
            frames_output.append(frame_entry)
        
        # ===== Assemble final data =====
        frustum_data = {
            "camera": camera_data,
            "frames": frames_output
        }
        
        # ===== Save JSON file =====
        output_path = os.path.join(self.output_dir, "frustum_data.json")
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(frustum_data, f, indent=2, ensure_ascii=False)
            unreal.log(f"[SUCCESS] Exported frustum data -> {output_path}")
        except Exception as e:
            unreal.log_error(f"[ERROR] Error exporting frustum_data.json: {e}")
    def _cleanup_callback(self):
        """Unregister callback to prevent memory leaks"""
        if self.callback_handle:
            unreal.unregister_slate_post_tick_callback(self.callback_handle)
            self.callback_handle = None


class ComprehensiveRenderer:
    """
    Comprehensive Batch Renderer
    ============================
    Manages the complete batch rendering workflow across multiple HDRI scenes,
    assets, and motion patterns.
    
    Rendering Order:
    1. Load map (once)
    2. For each HDRI scene:
       - Setup HDRI backdrop
       - Setup camera
       - For each asset:
         - For each motion pattern:
           - Spawn actor
           - Render animation
           - Collect data
    
    Output Structure:
    base_dir/
      +-- HDRI_Scene_1/
      |   +-- Asset_1/
      |   |   +-- motion_1/
      |   |   |   +-- frame_0000.png
      |   |   |   +-- animation_data.json
      |   |   +-- motion_2/
      |   +-- Asset_2/
      +-- HDRI_Scene_2/
    """
    
    def __init__(self, hdri_configs, base_output_dir):
        """
        Initialize batch renderer
        
        Args:
            hdri_configs: List of HDRI scene configurations
            base_output_dir: Base directory for all output files
        """
        self.hdri_configs = hdri_configs
        self.base_output_dir = base_output_dir
        
        # State tracking for nested loops
        self.current_hdri_index = 0
        self.current_asset_index = 0
        self.current_motion_index = 0
        
        self.spawned_actor = None
        self.map_loaded = False
        self.map_load_handle = None
        self.generated_actors = []

    def start(self):
        """Start the batch rendering process"""
        unreal.log("=" * 80)
        unreal.log("Starting Comprehensive Batch Rendering")
        unreal.log(f"Total HDRI Scenes: {len(self.hdri_configs)}")
        unreal.log("=" * 80)
        
        if self.hdri_configs:
            first_config = self.hdri_configs[0]
            map_path = first_config["map_path"]
            unreal.log(f"Loading map: {map_path}")
            
            if load_map(map_path):
                self.map_load_handle = unreal.register_slate_post_tick_callback(self._on_map_loaded)
            else:
                unreal.log_error(f"Failed to load map: {map_path}")

    def _on_map_loaded(self, _):
        """Callback when map loading completes"""
        if self.map_loaded:
            return
            
        if self.map_load_handle:
            unreal.unregister_slate_post_tick_callback(self.map_load_handle)
            self.map_load_handle = None
        
        self.map_loaded = True
        unreal.log("Map loaded successfully")
        self._process_next_hdri()

    def _process_next_hdri(self):
        """Process next HDRI scene (outer loop)"""
        if self.current_hdri_index >= len(self.hdri_configs):
            unreal.log("=" * 80)
            unreal.log("All rendering tasks completed successfully")
            unreal.log("=" * 80)
            return

        current_config = self.hdri_configs[self.current_hdri_index]
        hdri_name = current_config.get("name", f"HDRI_{self.current_hdri_index}")
        
        unreal.log("\n" + "=" * 80)
        unreal.log(f"HDRI Scene [{self.current_hdri_index + 1}/{len(self.hdri_configs)}]: {hdri_name}")
        unreal.log("=" * 80)

        # Clean up actors from previous HDRI scene
        if self.current_hdri_index > 0:
            prev_config = self.hdri_configs[self.current_hdri_index - 1]
            prev_hdri_name = prev_config.get("name", f"HDRI_{self.current_hdri_index - 1}")
            self._cleanup_hdri_actors(prev_hdri_name)

        # Setup HDRI backdrop
        if not self._setup_hdri_backdrop(current_config):
            unreal.log_error("Failed to setup HDRI, skipping...")
            self.current_hdri_index += 1
            self._process_next_hdri()
            return
        
        # Setup camera
        self._setup_camera(current_config)
        
        # Reset asset index and start processing assets
        self.current_asset_index = 0
        self._process_next_asset()

    def _cleanup_hdri_actors(self, hdri_name):
        """Clean up all actors from specified HDRI scene"""
        editor_actor_subs = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        all_actors = editor_actor_subs.get_all_level_actors()
        
        deleted_count = 0
        for actor in all_actors:
            try:
                label = actor.get_actor_label()
                if hdri_name in label:
                    unreal.log(f"Cleaning up previous HDRI actor: {label}")
                    editor_actor_subs.destroy_actor(actor)
                    deleted_count += 1
            except Exception as e:
                unreal.log_error(f"Error deleting actor: {e}")
        
        if deleted_count > 0:
            unreal.log(f"Cleaned up {deleted_count} actors from previous HDRI")

    def _process_next_asset(self):
        """Process next asset (middle loop)"""
        current_config = self.hdri_configs[self.current_hdri_index]
        assets = current_config.get("assets", [])
        
        if self.current_asset_index >= len(assets):
            # All assets processed for current HDRI, move to next HDRI
            hdri_name = current_config.get("name", f"HDRI_{self.current_hdri_index}")
            unreal.log(f"All assets rendered for HDRI scene '{hdri_name}'")
            self.current_hdri_index += 1
            self._process_next_hdri()
            return

        current_asset = assets[self.current_asset_index]
        asset_label = current_asset["label"]
        
        unreal.log(f"\n{'-' * 60}")
        unreal.log(f"Asset [{self.current_asset_index + 1}/{len(assets)}]: {asset_label}")
        unreal.log(f"{'-' * 60}")

        # Reset motion index and start processing motions
        self.current_motion_index = 0
        self._process_next_motion()

    def _process_next_motion(self):
        """Process next motion pattern (inner loop)"""
        current_config = self.hdri_configs[self.current_hdri_index]
        current_asset = current_config["assets"][self.current_asset_index]
        motions = current_asset.get("motions", [])
        
        if self.current_motion_index >= len(motions):
            # All motions processed for current asset, move to next asset
            
            self.current_asset_index += 1
            self._process_next_asset()
            return

        motion_type = motions[self.current_motion_index]
        
        # Clean up old actors
        self._cleanup_old_actors()
        
        # Spawn new actor
        if not self._spawn_actor():
            unreal.log_error("Failed to spawn actor, skipping...")
            self.current_motion_index += 1
            self._process_next_motion()
            return

        # Start animation rendering
        self._start_animation_render()

    def _setup_hdri_backdrop(self, config):
        """
        Setup HDRI backdrop for the scene
        
        Steps:
        1. Load HDRI Backdrop blueprint class
        2. Remove existing HDRI Backdrops
        3. Spawn new HDRI Backdrop
        4. Apply transform and texture
        5. Enable camera projection
        """
        editor_actor_subs = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        
        try:
            hdri_class_path = "/HDRIBackdrop/Blueprints/HDRIBackdrop.HDRIBackdrop_C"
            hdri_class = unreal.load_class(None, hdri_class_path)
            if not hdri_class:
                raise Exception(f"Failed to load class: {hdri_class_path}")

            # Remove existing HDRI Backdrops
            all_actors = editor_actor_subs.get_all_level_actors()
            existing_backdrops = [actor for actor in all_actors 
                                if actor.get_class().get_path_name() == hdri_class_path]
            
            for backdrop in existing_backdrops:
                editor_actor_subs.destroy_actor(backdrop)

            # Create new HDRI Backdrop
            hdri_transform = config["hdri_transform"]
            loc = hdri_transform["location"]
            rot = hdri_transform["rotation"]
            scale = hdri_transform.get("scale", {"x": 1, "y": 1, "z": 1})
            
            spawn_location = unreal.Vector(loc["x"], loc["y"], loc["z"])
            spawn_rotation = unreal.Rotator(pitch=rot["pitch"], yaw=rot["yaw"], roll=rot["roll"])
            spawn_scale = unreal.Vector(scale["x"], scale["y"], scale["z"])
            
            hdri_backdrop_actor = editor_actor_subs.spawn_actor_from_class(
                hdri_class, spawn_location, spawn_rotation
            )
            if not hdri_backdrop_actor:
                raise Exception("spawn_actor_from_class returned None")

            # Load and apply HDRI texture
            hdri_path = config["hdri_path"]
            hdri_asset = unreal.load_asset(hdri_path)
            if not hdri_asset:
                raise Exception(f"Failed to load HDRI asset: {hdri_path}")
            
            hdri_backdrop_actor.set_editor_property("cubemap", hdri_asset)
            hdri_backdrop_actor.set_actor_scale3d(spawn_scale)
            hdri_backdrop_actor.set_editor_property("UseCameraProjection", True)
            
            unreal.log(f"[SUCCESS] HDRI backdrop configured: {os.path.basename(hdri_path)}")
            return True

        except Exception as e:
            unreal.log_error(f"Failed to setup HDRI backdrop: {e}")
            return False

    def _setup_camera(self, config):
        """Setup editor viewport camera position and rotation"""
        camera_config = config.get("camera_config")
        if not camera_config:
            return
        
        loc = camera_config["location"]
        rot = camera_config["rotation"]
        
        camera_location = unreal.Vector(loc["x"], loc["y"], loc["z"])
        camera_rotation = unreal.Rotator(pitch=rot["pitch"], yaw=rot["yaw"], roll=rot["roll"])
        
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera_location, camera_rotation)
        unreal.log(f" Camera configured")

    def _cleanup_old_actors(self):
        """Clean up actors from previous motion pattern"""
        editor_actor_subs = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        all_actors = editor_actor_subs.get_all_level_actors()
        
        deleted_count = 0
        for actor in all_actors:
            try:
                label = actor.get_actor_label()
                
                # Match actors by HDRI name in label
                current_config = self.hdri_configs[self.current_hdri_index]
                hdri_name = current_config.get("name", f"HDRI_{self.current_hdri_index}")
                
                if hdri_name in label:
                    unreal.log(f"Deleting old actor: {label}")
                    editor_actor_subs.destroy_actor(actor)
                    deleted_count += 1
                    
            except Exception as e:
                unreal.log_error(f"Error deleting actor: {e}")
        
        unreal.log(f"Deleted {deleted_count} old actors")
        self.generated_actors.clear()

    def _spawn_actor(self):
        """
        Spawn actor for current asset and motion pattern
        
        Actor label format: {AssetLabel}_{HDRIName}_{MotionType}
        """
        current_config = self.hdri_configs[self.current_hdri_index]
        current_asset = current_config["assets"][self.current_asset_index]
        motions = current_asset["motions"]
        motion_type = motions[self.current_motion_index]
        
        # Get initial transform from HDRI-level motion_config
        motion_config = current_config["motion_config"]
        loc = motion_config["initial_location"]
        rot = motion_config["initial_rotation"]
        
        initial_location = unreal.Vector(loc["x"], loc["y"], loc["z"])
        
        hdri_name = current_config.get("name", f"HDRI_{self.current_hdri_index}")
        asset_label = current_asset["label"]
        
        actor_label = f"{asset_label}_{hdri_name}_{motion_type}"
        
        self.spawned_actor = spawn_static_mesh_actor(
            asset_path=current_asset["path"],
            location=initial_location,
            actor_label=actor_label
        )

        if not self.spawned_actor:
            return False

        # Record spawned actor
        self.generated_actors.append(self.spawned_actor)

        # Apply initial rotation
        initial_rotation = unreal.Rotator(pitch=rot["pitch"], yaw=rot["yaw"], roll=rot["roll"])
        self.spawned_actor.set_actor_rotation(initial_rotation, True)
        
        unreal.log(f" Actor spawned: {actor_label}")
        unreal.log(f"  Location: {initial_location}")
        unreal.log(f"  Rotation: pitch={rot['pitch']}, yaw={rot['yaw']}, roll={rot['roll']}")
        return True

    def _start_animation_render(self):
        """
        Start animation rendering for current actor and motion pattern
        
        Creates AnimationRenderer instance with parameters from configuration
        and sets up recursive callback for processing next motion pattern.
        """
        current_config = self.hdri_configs[self.current_hdri_index]
        current_asset = current_config["assets"][self.current_asset_index]
        motions = current_asset["motions"]
        motion_type = motions[self.current_motion_index]
        
        hdri_name = current_config.get("name", f"HDRI_{self.current_hdri_index}")
        asset_label = current_asset["label"]
        
        actor_label = f"{asset_label}_{hdri_name}_{motion_type}"
        
        # Prepare output directory structure
        output_dir = os.path.join(
            self.base_output_dir,
            hdri_name,
            asset_label,
            motion_type
        )
        
        # Build animation parameters from HDRI-level motion_config
        motion_config = current_config["motion_config"]
        animation_params = {
            "num_frames": motion_config["num_frames"],          # e.g. set to 21
            "total_distance": motion_config["total_distance"],
            "total_rotation": motion_config["total_rotation"],
            "y_amplitude": motion_config["y_amplitude"],
            "y_frequency": motion_config["y_frequency"],
            "motion_type": motion_type,
            "target_scale": current_asset["initial_scale"],
            "asset_path": current_asset["path"],
            "hdri_name": hdri_name,
            "hdri_path": current_config["hdri_path"],
            "camera_config": current_config.get("camera_config", {}),
            "prune_last_frame": True                            # Always delete last frame
        }

        def on_render_finished():
            """Callback when rendering completes - recursively process next motion"""

            self.current_motion_index += 1
            self._process_next_motion()

        # Create and start renderer
        renderer = AnimationRenderer(
            actor_label=actor_label,
            output_dir=output_dir,
            on_finished_callback=on_render_finished,
            **animation_params
        )
        renderer.start()


# =======================================================================================
# ===                       Configuration and Entry Point                            ===
# =======================================================================================

def load_config_from_json(config_path="render_config.json"):
    """
    Load rendering configuration from JSON file
    
    Args:
        config_path: Path to configuration JSON file (relative to script directory)
    
    Returns:
        Tuple of (hdri_configs, output_directory)
    """
    try:
        # Get absolute path to config file
        if not os.path.isabs(config_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, config_path)
        
        # Load JSON configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        hdri_configs = config.get("hdri_scenes", [])
        output_directory = config.get("output_directory", "D:/ue5/projects/first/Saved/Screenshots")
        
        unreal.log(f" Loaded configuration from: {config_path}")
        unreal.log(f"   HDRI Scenes: {len(hdri_configs)}")
        unreal.log(f"   Output Directory: {output_directory}")
        
        return hdri_configs, output_directory
        
    except FileNotFoundError:
        unreal.log_error(f" Configuration file not found: {config_path}")
        unreal.log_error("Please create render_config.json in the script directory")
        return [], ""
    except json.JSONDecodeError as e:
        unreal.log_error(f" Invalid JSON in configuration file: {e}")
        return [], ""
    except Exception as e:
        unreal.log_error(f" Error loading configuration: {e}")
        return [], ""


if __name__ == "__main__":
    # Load configuration from JSON file
    hdri_configs, output_directory = load_config_from_json("render_config.json")
    
    if not hdri_configs or not output_directory:
        unreal.log_error("Failed to load configuration. Aborting.")
    else:
        # Start rendering
        renderer = ComprehensiveRenderer(hdri_configs, output_directory)
        renderer.start()