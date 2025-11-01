"""
Level/Map handling utilities
"""
import unreal

def load_map(map_asset_path):
    """
    Load the specified map.

    Before loading a new map, it will prompt to save any unsaved levels.

    :param map_asset_path: Full path to the map asset (e.g., /Game/ThirdPerson/Maps/ThirdPersonMap.ThirdPersonMap)
    :return: Returns True on success, False on failure
    """
    unreal.log(f"Preparing to load map: {map_asset_path}")

    # Get the editor subsystem
    editor_level_lib = unreal.EditorLevelLibrary()

    # Check if the asset exists and provide a clearer error message
    if not unreal.EditorAssetLibrary.does_asset_exist(map_asset_path):
        unreal.log_error(f"Map asset does not exist, please check the path: {map_asset_path}")
        return False

    # Execute the load operation
    # This will load the new level. If the current level has modifications, the editor will prompt the user to save
    success = editor_level_lib.load_level(map_asset_path)

    if success:
        unreal.log(f"Successfully sent command to load map: {map_asset_path}")
    else:
        # Note: If the user selects "Cancel" in the save dialog, load_level may also return False
        unreal.log_error(f"Failed to load map. User may have cancelled the operation, or the path is invalid: {map_asset_path}")

    return success
