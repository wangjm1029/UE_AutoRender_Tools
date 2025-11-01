# UE Auto-Render & Frustum Visualization Tools

A collection of lightweight Python scripts for Unreal Engine to automate rendering tasks and visualize camera/object poses.

## Key Features

### 1. Auto-Render Script

* **Lightweight & CPU-Only:** Runs efficiently without requiring a dedicated GPU, relying only on the CPU.
* **Powerful Batch Processing:** Easily create combinations for large-scale rendering tasks. You can mix and match:
    * Different objects (actors)
    * Various motion patterns
    * Multiple HDRI backgrounds

### 2. Frustum & Pose Visualization Script

* **Direct 6D Pose Import:** Natively supports UE camera and object 6D pose data (position and rotation).
* **No Coordinate System Conversion:** Saves time and avoids errors. You can import your pose data directly without worrying about transforming it between different coordinate systems (e.g., from external tools to UE).
* ## How to Use

This project contains two main scripts with different setup requirements.

---

### 1. Auto-Render Script (Runs in UE)

This script is designed to be run directly inside the Unreal Editor.

#### Prerequisites

* **Unreal Engine 5.1** (or later).
* **UE Python Plugin:** You must enable this plugin first.
    1.  In the UE editor, go to `Edit` > `Plugins`.
    2.  Search for "Python" and check the box for `Python Editor Script Plugin`.
    3.  Restart the editor if prompted.

#### Setup (Preparing the Scene)

1.  **Align Ground Plane:** Adjust your HDRI background so that its "ground" visually aligns with the motion plane of your objects. This ensures correct reflections and lighting.
2.  **Find Your Camera Pose (Optional):**
    * To set a specific camera position for rendering, first position your camera in the editor viewport.
    * Run the `get_camera.py` script (see "Running" section below).
    * This will output the 6D pose (position and rotation) of your current viewport camera.
    * Copy this pose data to your configuration file to define the camera's position for batch rendering.

#### Running the Script

1.  In the UE Editor, click `Tools` in the main top menu.
2.  Scroll down and select `Execute Python Script`.
3.  Navigate to this project's folder and select the `auto_render.py` script to run it.

---

### 2. Frustum & Pose Visualization Script (Runs Externally)

This script is a standalone tool (using PyVista and NumPy) and runs outside of Unreal Engine, in its own Python environment.

#### Environment Setup

This script requires a specific Conda environment.

1.  Open your terminal or Anaconda Prompt.
2.  Create the environment (this only needs to be done once):
    ```bash
    conda create -n frustum_visualize python=3.10
    ```
3.  Activate the new environment:
    ```bash
    conda activate frustum_visualize
    ```
4.  Install the required libraries:
    ```bash
    pip install numpy pyvista
    ```

#### Running the Script

1.  Make sure your Conda environment is active: `conda activate frustum_visualize`
2.  Navigate to the project directory in your terminal.
3.  Run the script:
    ```bash
    python frustum_visualizer.py
    ```
    *(Note: You will likely need to edit the `frustum_visualizer.py` script or pass it arguments to load your specific 6D pose data.)*
## Current Limitations & Future Roadmap

### Current Limitations: Background Complexity

The current version of the auto-render script is designed to be lightweight and fast, primarily by using **HDRI maps for backgrounds**.

This approach has a significant trade-off:
* **It sacrifices background complexity for speed and simplicity.**
* HDRI maps are 2D projections and lack true 3D geometry. This means they cannot provide dynamic background elements, real-time parallax, or complex interactions (like an object moving *behind* a 3D background element).
* While excellent for simple object rendering, this method cannot match the visual fidelity of top-tier research projects that load and render **entire 3D levels (关卡)** as the background.

### Future Roadmap: Server-Side Data Generation

The long-term vision for this project is to evolve it into a robust, **server-side data generation pipeline** suitable for training large-scale models.

The next major goals are:

* **Develop a "server version":** This version will be designed for headless operation (running without a visible editor) on servers.
* **Support for 3D Levels:** Move beyond HDRI maps to support programmatic loading, swapping, and managing of full 3D environments.
* **Target Quality:** The ultimate goal is to produce high-fidelity, large-scale datasets that meet the quality standards required for training state-of-the-art models (such as those used by `Object Mover` or `SynCamMaster`).
