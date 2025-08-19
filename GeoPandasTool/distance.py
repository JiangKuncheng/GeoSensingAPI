import geopandas as gpd
import json
import os
from typing import Union, List, Dict
from shapely.geometry import shape


def distance(geojson_names: Union[str, List[str]], other_geojson_name: str) -> Union[List[float], Dict[str, List[float]]]:
    """
    计算一个或多个 GeoJSON 文件中每个几何对象到另一个 GeoJSON 文件中几何对象的距离

    参数:
        geojson_names (Union[str, List[str]]):
            - 单个 GeoJSON 文件名（不含路径和扩展名）
            - 或多个文件名组成的列表
        other_geojson_name (str): 目标 GeoJSON 文件名

    返回:
        Union[List[float], Dict[str, List[float]]]:
            - 如果传入单个名称，返回对应的距离列表
            - 如果传入多个名称，返回字典，键为输入文件名，值为对应距离列表
    """
    # 如果是单个字符串，转为列表处理
    is_single = isinstance(geojson_names, str)
    names = [geojson_names] if is_single else geojson_names
    results = {}

    # 读取目标 GeoJSON 文件
    other_path = os.path.join("geojson", f"{other_geojson_name}.geojson")
    with open(other_path, "r", encoding="utf-8") as f:
        other_geojson_data = json.load(f)
    
    # 提取目标几何对象（使用第一个几何对象作为参考点）
    if other_geojson_data.get("type") == "FeatureCollection":
        other_geom = shape(other_geojson_data["features"][0]["geometry"])
    elif other_geojson_data.get("type") == "Feature":
        other_geom = shape(other_geojson_data["geometry"])
    else:
        raise ValueError("目标 GeoJSON 不包含 Feature 或 FeatureCollection")

    for name in names:
        input_path = os.path.join("geojson", f"{name}.geojson")
        
        try:
            # 读取输入GeoJSON文件
            with open(input_path, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)

            # 提取所有 geometry
            geometries = []
            if geojson_data.get("type") == "FeatureCollection":
                for feature in geojson_data["features"]:
                    geom = shape(feature["geometry"])
                    geometries.append(geom)
            elif geojson_data.get("type") == "Feature":
                geom = shape(geojson_data["geometry"])
                geometries.append(geom)
            else:
                raise ValueError("输入的 GeoJSON 不包含 Feature 或 FeatureCollection")

            if not geometries:
                raise ValueError("GeoJSON 中未找到有效的 geometry")

            # 构建 GeoSeries
            gseries = gpd.GeoSeries(geometries)

            # 计算距离
            results[name] = gseries.distance(other_geom).tolist()
            
        except Exception as e:
            results[name] = f"Error: {str(e)}"

    return results[geojson_names] if is_single else results
