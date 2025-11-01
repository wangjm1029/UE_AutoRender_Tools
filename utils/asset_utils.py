"""
资产处理工具集
"""
import unreal

def spawn_static_mesh_actor(asset_path, location=unreal.Vector(0, 0, 0), 
                            rotation=unreal.Rotator(0, 0, 0), 
                            scale=unreal.Vector(1.0, 1.0, 1.0), 
                            actor_label="MySpawnedActor"):
    """
    在场景中生成一个静态网格体Actor。

    :param asset_path: 静态网格体资产的完整路径 (例如, /Game/StarterContent/Shapes/Shape_Cube.Shape_Cube)
    :param location: 生成位置 (unreal.Vector)
    :param rotation: 生成旋转 (unreal.Rotator)
    :param scale: 生成缩放 (unreal.Vector)
    :param actor_label: 在编辑器中为Actor设置的标签名
    :return: 成功则返回生成的Actor对象，失败则返回None
    """
    # 1. 加载资产
    static_mesh_asset = unreal.load_asset(asset_path)
    if not static_mesh_asset:
        unreal.log_error(f"无法加载资产,请检查路径: {asset_path}")
        return None

    # 2. 生成一个空的 StaticMeshActor
    editor_level_lib = unreal.EditorLevelLibrary()
    new_actor = editor_level_lib.spawn_actor_from_class(
        unreal.StaticMeshActor.static_class(),
        location,
        rotation
    )
    if not new_actor:
        unreal.log_error("生成Actor失败!")
        return None

    # 3. 将模型赋给Actor
    static_mesh_component = new_actor.static_mesh_component
    static_mesh_component.set_static_mesh(static_mesh_asset)

    # 4. 设置其他属性
    new_actor.set_actor_scale3d(scale)
    new_actor.set_actor_label(actor_label)
    
    unreal.log(f"成功生成Actor '{actor_label}' 并设置模型。")
    return new_actor


def spawn_skeletal_mesh_actor(asset_path, location=unreal.Vector(0, 0, 0), 
                              rotation=unreal.Rotator(0, 0, 0), 
                              scale=unreal.Vector(1.0, 1.0, 1.0), 
                              actor_label="MySkeletalActor"):
    """
    在场景中生成一个骨骼网格体Actor。

    :param asset_path: 骨骼网格体资产的完整路径 (例如, /Game/ForestAnimalsPack/Bear/Meshes/SK_Bear.SK_Bear)
    :param location: 生成位置 (unreal.Vector)
    :param rotation: 生成旋转 (unreal.Rotator)
    :param scale: 生成缩放 (unreal.Vector)
    :param actor_label: 在编辑器中为Actor设置的标签名
    :return: 成功则返回生成的Actor对象,失败则返回None
    """
    # 1. 加载骨骼网格体资产
    skeletal_mesh_asset = unreal.load_asset(asset_path)
    if not skeletal_mesh_asset:
        unreal.log_error(f"无法加载骨骼网格体资产,请检查路径: {asset_path}")
        return None
    
    # 验证资产类型
    if not isinstance(skeletal_mesh_asset, unreal.SkeletalMesh):
        unreal.log_error(f"资产不是骨骼网格体类型: {asset_path}")
        return None

    # 2. 生成一个空的 SkeletalMeshActor
    editor_level_lib = unreal.EditorLevelLibrary()
    new_actor = editor_level_lib.spawn_actor_from_class(
        unreal.SkeletalMeshActor.static_class(),
        location,
        rotation
    )
    if not new_actor:
        unreal.log_error("生成SkeletalMeshActor失败!")
        return None

    # 3. 获取SkeletalMeshComponent并设置骨骼网格体
    skeletal_mesh_component = new_actor.skeletal_mesh_component
    if skeletal_mesh_component:
        skeletal_mesh_component.set_skeletal_mesh(skeletal_mesh_asset)
    else:
        unreal.log_error("无法获取SkeletalMeshComponent!")
        editor_level_lib.destroy_actor(new_actor)
        return None

    # 4. 设置其他属性
    new_actor.set_actor_scale3d(scale)
    new_actor.set_actor_label(actor_label)
    
    unreal.log(f"成功生成骨骼网格体Actor '{actor_label}'。")
    return new_actor


def spawn_mesh_actor(asset_path, location=unreal.Vector(0, 0, 0), 
                    rotation=unreal.Rotator(0, 0, 0), 
                    scale=unreal.Vector(1.0, 1.0, 1.0), 
                    actor_label="MyActor"):
    """
    智能生成网格体Actor,自动检测是静态网格体还是骨骼网格体。

    :param asset_path: 网格体资产的完整路径
    :param location: 生成位置 (unreal.Vector)
    :param rotation: 生成旋转 (unreal.Rotator)
    :param scale: 生成缩放 (unreal.Vector)
    :param actor_label: 在编辑器中为Actor设置的标签名
    :return: 成功则返回生成的Actor对象,失败则返回None
    """
    # 加载资产
    mesh_asset = unreal.load_asset(asset_path)
    if not mesh_asset:
        unreal.log_error(f"无法加载资产: {asset_path}")
        return None
    
    # 根据资产类型调用相应的函数
    if isinstance(mesh_asset, unreal.SkeletalMesh):
        unreal.log(f"检测到骨骼网格体,使用SkeletalMeshActor: {asset_path}")
        return spawn_skeletal_mesh_actor(asset_path, location, rotation, scale, actor_label)
    elif isinstance(mesh_asset, unreal.StaticMesh):
        unreal.log(f"检测到静态网格体,使用StaticMeshActor: {asset_path}")
        return spawn_static_mesh_actor(asset_path, location, rotation, scale, actor_label)
    else:
        unreal.log_error(f"不支持的网格体类型: {type(mesh_asset).__name__}")
        return None