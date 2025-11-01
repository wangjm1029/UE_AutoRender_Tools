"""
关卡/地图处理工具集
"""
import unreal

def load_map(map_asset_path):
    """
    加载指定的地图。

    在加载新地图前，会提示保存当前未保存的关卡。

    :param map_asset_path: 地图资产的完整路径 (例如, /Game/ThirdPerson/Maps/ThirdPersonMap.ThirdPersonMap)
    :return: 成功则返回True，失败则返回False
    """
    unreal.log(f"准备加载地图: {map_asset_path}")

    # 获取编辑器子系统
    editor_level_lib = unreal.EditorLevelLibrary()

    # 检查资产是否存在，提供更明确的错误信息
    if not unreal.EditorAssetLibrary.does_asset_exist(map_asset_path):
        unreal.log_error(f"地图资产不存在，请检查路径: {map_asset_path}")
        return False

    # 执行加载操作
    # 这会加载新关卡，如果当前关卡有修改，编辑器会弹出对话框提示用户保存
    success = editor_level_lib.load_level(map_asset_path)

    if success:
        unreal.log(f"成功发送加载地图的指令: {map_asset_path}")
    else:
        # 请注意：如果用户在弹出的保存对话框中选择“取消”，load_level也可能返回False
        unreal.log_error(f"加载地图指令失败。可能是用户取消了操作，或者路径无效: {map_asset_path}")

    return success
