import geopandas as gpd
import json
import os
from typing import Union, List, Dict
from shapely.geometry import shape, Polygon, MultiPolygon


def exterior(geojson_names: Union[str, List[str]]) -> Union[List, Dict[str, List]]:
    """
    提取一个或多个 GeoJSON 文件中的 Polygon / MultiPolygon 的外边界

    参数:
        geojson_names (Union[str, List[str]]):
            - 单个 GeoJSON 文件名（不含路径和扩展名）
            - 或多个文件名组成的列表

    返回:
        Union[List, Dict[str, List]]:
            - 如果传入单个名称，返回对应的外边界列表
            - 如果传入多个名称，返回字典，键为输入文件名，值为对应外边界列表
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
                raise ValueError("输入的 GeoJSON 不包含 Feature 或 FeatureCollection")

            if not geometries:
                raise ValueError("GeoJSON 中未找到有效的 geometry")

            # 构建 GeoSeries
            gseries = gpd.GeoSeries(geometries)

            # 提取 exterior，非 Polygon/MultiPolygon 返回 None
            exteriors = []
            for geom in gseries:
                if geom.geom_type == 'Polygon':
                    exteriors.append(geom.exterior)
                elif geom.geom_type == 'MultiPolygon':
                    exteriors.append([poly.exterior for poly in geom.geoms])
                else:
                    exteriors.append(None)

            results[name] = exteriors
            
        except Exception as e:
            results[name] = f"Error: {str(e)}"

    return results[geojson_names] if is_single else results
