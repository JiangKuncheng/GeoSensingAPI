import geopandas as gpd
import json
import os
from typing import Union, List, Dict
from shapely.geometry import shape

def dwithin(geojson_names: Union[str, List[str]], other_geojson_name: str, distance: float) -> Union[bool, Dict[str, bool]]:
    """
    判断一个或多个 GeoJSON 文件中的几何对象是否在另一个 GeoJSON 文件中几何对象的指定距离内

    参数:
        geojson_names (Union[str, List[str]]):
            - 单个 GeoJSON 文件名（不含路径和扩展名）
            - 或多个文件名组成的列表
        other_geojson_name (str): 目标 GeoJSON 文件名
        distance (float): 距离阈值，单位为度或米（根据坐标系决定）

    返回:
        Union[bool, Dict[str, bool]]:
            - 如果传入单个名称，返回对应的布尔值结果
            - 如果传入多个名称，返回字典，键为输入文件名，值为对应布尔值结果
    """
    # 如果是单个字符串，转为列表处理
    is_single = isinstance(geojson_names, str)
    names = [geojson_names] if is_single else geojson_names
    results = {}

    # 读取目标 GeoJSON 文件
    other_path = os.path.join("geojson", f"{other_geojson_name}.geojson")
    with open(other_path, "r", encoding="utf-8") as f:
        other_geojson_data = json.load(f)
    other_geometries = [shape(feature["geometry"]) for feature in other_geojson_data["features"]]

    for name in names:
        input_path = os.path.join("geojson", f"{name}.geojson")
        
        try:
            # 读取输入GeoJSON文件
            with open(input_path, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)

            # 提取几何对象
            geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]]

            # 构建 GeoSeries
            gseries = gpd.GeoSeries(geometries)

            # 检查是否在指定距离内
            result = []
            for geometry in gseries:
                result.append(any(geometry.dwithin(other_geometry, distance) for other_geometry in other_geometries))

            # 返回整体结果（任一几何对象在指定距离内）
            results[name] = any(result)
            
        except Exception as e:
            results[name] = f"Error: {str(e)}"

    return results[geojson_names] if is_single else results
