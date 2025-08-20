import geopandas as gpd
import json
import os
from typing import Union, List, Dict
from shapely.geometry import shape

def touches(geojson_names: Union[str, List[str]], other_geojson_name: str) -> Union[bool, Dict[str, bool]]:
    """
    判断一个或多个 GeoJSON 文件中的几何对象是否仅在边界上接触另一个 GeoJSON 文件中的几何对象

    参数:
        geojson_names (Union[str, List[str]]):
            - 单个 GeoJSON 文件名（不含路径和扩展名）
            - 或多个文件名组成的列表
        other_geojson_name (str): 目标 GeoJSON 文件名，判断主几何是否与其接触

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
            other_series = gpd.GeoSeries(other_geometries)

            # 判断是否仅在边界上接触
            result = []
            for geometry in gseries:
                result.append(any(geometry.touches(other) for other in other_series))

            # 返回整体结果（任一几何对象与目标几何接触）
            results[name] = any(result)
            
        except Exception as e:
            results[name] = f"Error: {str(e)}"

    return results[geojson_names] if is_single else results
