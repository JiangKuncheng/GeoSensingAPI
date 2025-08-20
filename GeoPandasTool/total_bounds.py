import geopandas as gpd
import json
import os
from typing import Union, List, Dict
from shapely.geometry import shape


def total_bounds(geojson_names: Union[str, List[str]]) -> Union[List[float], Dict[str, List[float]]]:
    """
    计算一个或多个 GeoJSON 文件中所有几何对象的整体包围盒

    参数:
        geojson_names (Union[str, List[str]]):
            - 单个 GeoJSON 文件名（不含路径和扩展名）
            - 或多个文件名组成的列表

    返回:
        Union[List[float], Dict[str, List[float]]]:
            - 如果传入单个名称，返回对应的包围盒 [minx, miny, maxx, maxy]
            - 如果传入多个名称，返回字典，键为输入文件名，值为对应包围盒
    """
    # 如果是单个字符串，转为列表处理
    is_single = isinstance(geojson_names, str)
    names = [geojson_names] if is_single else geojson_names
    results = {}

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
                raise ValueError("输入的GeoJSON不包含Feature或FeatureCollection")

            if not geometries:
                raise ValueError("GeoJSON中未找到有效的geometry")

            # 构建 GeoSeries
            gseries = gpd.GeoSeries(geometries)

            # 计算 total_bounds
            results[name] = gseries.total_bounds.tolist()
            
        except Exception as e:
            results[name] = f"Error: {str(e)}"

    return results[geojson_names] if is_single else results
