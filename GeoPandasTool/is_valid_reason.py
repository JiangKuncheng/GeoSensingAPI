import geopandas as gpd
import json
import os
from typing import Union, List, Dict
from shapely.geometry import shape

def is_valid_reason(geojson_names: Union[str, List[str]]) -> Union[List[str], Dict[str, List[str]]]:
    """
    返回一个或多个 GeoJSON 文件中的每个几何对象的合法性检查原因

    参数:
        geojson_names (Union[str, List[str]]):
            - 单个 GeoJSON 文件名（不含路径和扩展名）
            - 或多个文件名组成的列表

    返回:
        Union[List[str], Dict[str, List[str]]]:
            - 如果传入单个名称，返回对应的合法性检查结果列表
            - 如果传入多个名称，返回字典，键为输入文件名，值为对应合法性检查结果列表
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

            geometries = []
            if geojson_data.get("type") == "FeatureCollection":
                for feature in geojson_data["features"]:
                    geometries.append(shape(feature["geometry"]))
            elif geojson_data.get("type") == "Feature":
                geometries.append(shape(geojson_data["geometry"]))
            else:
                raise ValueError("输入的 GeoJSON 不包含 Feature 或 FeatureCollection")

            # 检查每个几何图形的合法性原因
            validity_reasons = []
            for geom in geometries:
                try:
                    if geom.is_valid:
                        validity_reasons.append("Valid")
                    else:
                        # 使用 explain_validity() 方法获取无效原因
                        validity_reasons.append(geom.explain_validity())
                except Exception as e:
                    validity_reasons.append(f"Error: {str(e)}")
            
            results[name] = validity_reasons
            
        except Exception as e:
            results[name] = f"Error: {str(e)}"

    return results[geojson_names] if is_single else results
