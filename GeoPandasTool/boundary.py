import geopandas as gpd
import json
import os
from typing import Union, List, Dict
from shapely.geometry import shape


def boundary(geojson_names: Union[str, List[str]]) -> Union[str, Dict[str, str]]:
    """
    计算一个或多个 GeoJSON 文件的边界并保存为文件

    参数:
        geojson_names (Union[str, List[str]]):
            - 单个 GeoJSON 文件名（不含路径和扩展名）
            - 或多个文件名组成的列表

    返回:
        Union[str, Dict[str, str]]:
            - 如果传入单个名称，返回对应的输出文件名
            - 如果传入多个名称，返回字典，键为输入文件名，值为对应输出文件名
    """
    # 如果是单个字符串，转为列表处理
    is_single = isinstance(geojson_names, str)
    names = [geojson_names] if is_single else geojson_names
    results = {}

    for name in names:
        input_path = os.path.join("geojson", f"{name}.geojson")
        output_name = f"{name}_boundary"
        output_path = os.path.join("geojson", f"{output_name}.geojson")
        
        with open(input_path, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
        
        geometries = _extract_geometries(geojson_data)
        gseries = gpd.GeoSeries(geometries)
        boundary_geoms = gseries.boundary
        
        # 转换为 GeoJSON 并保存
        boundary_features = []
        for geom in boundary_geoms:
            if not geom.is_empty:
                boundary_features.append({
                    "type": "Feature",
                    "geometry": json.loads(geom.to_json()),
                    "properties": {}
                })
        
        boundary_geojson = {
            "type": "FeatureCollection",
            "features": boundary_features
        }
        
        # 保存到文件
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(boundary_geojson, f, ensure_ascii=False, indent=2)
        
        results[name] = output_name

    return results[geojson_names] if is_single else results


def _extract_geometries(geojson):
    geometries = []
    if geojson.get("type") == "FeatureCollection":
        for feature in geojson["features"]:
            geom = shape(feature["geometry"])
            if geom.geom_type in ["Polygon", "MultiPolygon"]:
                geometries.append(geom)
    elif geojson.get("type") == "Feature":
        geom = shape(geojson["geometry"])
        if geom.geom_type in ["Polygon", "MultiPolygon"]:
            geometries.append(geom)

    if not geometries:
        raise ValueError("未找到 Polygon 或 MultiPolygon")
    return geometries