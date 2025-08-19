import geopandas as gpd
import json
import os
from typing import Union, List, Dict
from shapely.geometry import shape

def covered_by(geojson_names: Union[str, List[str]], container_geojson_name: str) -> Union[bool, Dict[str, bool]]:
    """
    判断一个或多个 GeoJSON 文件中的几何对象是否被另一个 GeoJSON 文件中的几何对象完全覆盖

    参数:
        geojson_names (Union[str, List[str]]):
            - 单个 GeoJSON 文件名（不含路径和扩展名）
            - 或多个文件名组成的列表
        container_geojson_name (str): 作为容器的 GeoJSON 文件名

    返回:
        Union[bool, Dict[str, bool]]:
            - 如果传入单个名称，返回对应的布尔值结果
            - 如果传入多个名称，返回字典，键为输入文件名，值为对应布尔值结果
    """
    # 如果是单个字符串，转为列表处理
    is_single = isinstance(geojson_names, str)
    names = [geojson_names] if is_single else geojson_names
    results = {}

    # 读取容器 GeoJSON 文件
    container_path = os.path.join("geojson", f"{container_geojson_name}.geojson")
    with open(container_path, "r", encoding="utf-8") as f:
        container_geojson_data = json.load(f)
    container_geometries = [shape(feature["geometry"]) for feature in container_geojson_data["features"]]

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
            container_series = gpd.GeoSeries(container_geometries)

            # 判断是否被覆盖
            result = []
            for geometry in gseries:
                result.append(any(geometry.covered_by(container) for container in container_series))

            # 返回整体结果（所有几何对象都被容器覆盖）
            results[name] = all(result)
            
        except Exception as e:
            results[name] = f"Error: {str(e)}"

    return results[geojson_names] if is_single else results
