"""
Asset handling utilities
"""
import unreal

def spawn_static_mesh_actor(asset_path, location=unreal.Vector(0, 0, 0), 
                            rotation=unreal.Rotator(0, 0, 0), 
                            scale=unreal.Vector(1.0, 1.0, 1.0), 
                            actor_label="MySpawnedActor"):
    """
    Spawn a static mesh actor in the scene.

    :param asset_path: Full path to the static mesh asset (e.g., /Game/StarterContent/Shapes/Shape_Cube.Shape_Cube)
    :param location: Spawn location (unreal.Vector)
    :param rotation: Spawn rotation (unreal.Rotator)
    :param scale: Spawn scale (unreal.Vector)
    :param actor_label: Label name for the actor in the editor
    :return: Returns the spawned Actor object on success, None on failure
    """
    # 1. Load the asset
    static_mesh_asset = unreal.load_asset(asset_path)
    if not static_mesh_asset:
        unreal.log_error(f"Failed to load asset, please check the path: {asset_path}")
        return None

    # 2. Spawn an empty StaticMeshActor
    editor_level_lib = unreal.EditorLevelLibrary()
    new_actor = editor_level_lib.spawn_actor_from_class(
        unreal.StaticMeshActor.static_class(),
        location,
        rotation
    )
    if not new_actor:
        unreal.log_error("Failed to spawn Actor!")
        return None

    # 3. Assign the mesh to the actor
    static_mesh_component = new_actor.static_mesh_component
    static_mesh_component.set_static_mesh(static_mesh_asset)

    # 4. Set other properties
    new_actor.set_actor_scale3d(scale)
    new_actor.set_actor_label(actor_label)
    
    unreal.log(f"Successfully spawned Actor '{actor_label}' and set the mesh.")
    return new_actor


def spawn_skeletal_mesh_actor(asset_path, location=unreal.Vector(0, 0, 0), 
                              rotation=unreal.Rotator(0, 0, 0), 
                              scale=unreal.Vector(1.0, 1.0, 1.0), 
                              actor_label="MySkeletalActor"):
    """
    Spawn a skeletal mesh actor in the scene.

    :param asset_path: Full path to the skeletal mesh asset (e.g., /Game/ForestAnimalsPack/Bear/Meshes/SK_Bear.SK_Bear)
    :param location: Spawn location (unreal.Vector)
    :param rotation: Spawn rotation (unreal.Rotator)
    :param scale: Spawn scale (unreal.Vector)
    :param actor_label: Label name for the actor in the editor
    :return: Returns the spawned Actor object on success, None on failure
    """
    # 1. Load the skeletal mesh asset
    skeletal_mesh_asset = unreal.load_asset(asset_path)
    if not skeletal_mesh_asset:
        unreal.log_error(f"Failed to load skeletal mesh asset, please check the path: {asset_path}")
        return None
    
    # Validate asset type
    if not isinstance(skeletal_mesh_asset, unreal.SkeletalMesh):
        unreal.log_error(f"Asset is not a skeletal mesh type: {asset_path}")
        return None

    # 2. Spawn an empty SkeletalMeshActor
    editor_level_lib = unreal.EditorLevelLibrary()
    new_actor = editor_level_lib.spawn_actor_from_class(
        unreal.SkeletalMeshActor.static_class(),
        location,
        rotation
    )
    if not new_actor:
        unreal.log_error("Failed to spawn SkeletalMeshActor!")
        return None

    # 3. Get SkeletalMeshComponent and set the skeletal mesh
    skeletal_mesh_component = new_actor.skeletal_mesh_component
    if skeletal_mesh_component:
        skeletal_mesh_component.set_skeletal_mesh(skeletal_mesh_asset)
    else:
        unreal.log_error("Failed to get SkeletalMeshComponent!")
        editor_level_lib.destroy_actor(new_actor)
        return None

    # 4. Set other properties
    new_actor.set_actor_scale3d(scale)
    new_actor.set_actor_label(actor_label)
    
    unreal.log(f"Successfully spawned skeletal mesh Actor '{actor_label}'.")
    return new_actor


def spawn_mesh_actor(asset_path, location=unreal.Vector(0, 0, 0), 
                    rotation=unreal.Rotator(0, 0, 0), 
                    scale=unreal.Vector(1.0, 1.0, 1.0), 
                    actor_label="MyActor"):
    """
    Intelligently spawn a mesh actor, automatically detecting whether it's a static mesh or skeletal mesh.

    :param asset_path: Full path to the mesh asset
    :param location: Spawn location (unreal.Vector)
    :param rotation: Spawn rotation (unreal.Rotator)
    :param scale: Spawn scale (unreal.Vector)
    :param actor_label: Label name for the actor in the editor
    :return: Returns the spawned Actor object on success, None on failure
    """
    # Load the asset
    mesh_asset = unreal.load_asset(asset_path)
    if not mesh_asset:
        unreal.log_error(f"Failed to load asset: {asset_path}")
        return None
    
    # Call the appropriate function based on asset type
    if isinstance(mesh_asset, unreal.SkeletalMesh):
        unreal.log(f"Detected skeletal mesh, using SkeletalMeshActor: {asset_path}")
        return spawn_skeletal_mesh_actor(asset_path, location, rotation, scale, actor_label)
    elif isinstance(mesh_asset, unreal.StaticMesh):
        unreal.log(f"Detected static mesh, using StaticMeshActor: {asset_path}")
        return spawn_static_mesh_actor(asset_path, location, rotation, scale, actor_label)
    else:
        unreal.log_error(f"Unsupported mesh type: {type(mesh_asset).__name__}")
        return None