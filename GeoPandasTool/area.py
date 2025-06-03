import json
from typing import Union, List, Dict
from shapely.geometry import shape, Polygon, MultiPolygon
import geopandas as gpd

def area(geojson_paths: Union[str, List[str]]) -> Dict[str, float]:
    """
    计算一个或多个本地 GeoJSON 文件中 Polygon/MultiPolygon 的总面积（平方米），自动修复坐标顺序错误。

    参数:
        geojson_paths (Union[str, List[str]]):
            - 单个本地 GeoJSON 文件路径
            - 或多个路径组成的列表

    返回:
        Dict[str, float]:
            键为路径，值为该文件中所有有效 Polygon/MultiPolygon 的总面积（平方米）
    """
    paths = [geojson_paths] if isinstance(geojson_paths, str) else geojson_paths
    results = {}

    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            geojson = json.load(f)

        geometries = []

        if geojson.get("type") == "FeatureCollection":
            for feature in geojson["features"]:
                geom = shape(feature["geometry"])
                # 修复 Polygon 坐标顺序（外环逆时针，内环顺时针）
                if geom.geom_type == "Polygon":
                    # 提取外环和内环
                    exterior = geom.exterior.coords[:]
                    interiors = [interior.coords[:] for interior in geom.interiors]
                    # 确保外环逆时针（若顺时针则反转）
                    if not is_counterclockwise(exterior):
                        exterior = list(reversed(exterior))
                    # 确保内环顺时针（若逆时针则反转）
                    for i in range(len(interiors)):
                        if is_counterclockwise(interiors[i]):
                            interiors[i] = list(reversed(interiors[i]))
                    # 重建 Polygon
                    valid_geom = Polygon(exterior, interiors)
                    geometries.append(valid_geom)
                elif geom.geom_type == "MultiPolygon":
                    # 对每个子 Polygon 应用同样逻辑
                    valid_polygons = []
                    for poly in geom.geoms:
                        exterior = poly.exterior.coords[:]
                        interiors = [interior.coords[:] for interior in poly.interiors]
                        if not is_counterclockwise(exterior):
                            exterior = list(reversed(exterior))
                        for i in range(len(interiors)):
                            if is_counterclockwise(interiors[i]):
                                interiors[i] = list(reversed(interiors[i]))
                        valid_polygons.append(Polygon(exterior, interiors))
                    valid_geom = MultiPolygon(valid_polygons)
                    geometries.append(valid_geom)
        elif geojson.get("type") == "Feature":
            geom = shape(geojson["geometry"])
            # 同上处理单个几何对象
            if geom.geom_type == "Polygon":
                exterior = geom.exterior.coords[:]
                interiors = [interior.coords[:] for interior in geom.interiors]
                if not is_counterclockwise(exterior):
                    exterior = list(reversed(exterior))
                for i in range(len(interiors)):
                    if is_counterclockwise(interiors[i]):
                        interiors[i] = list(reversed(interiors[i]))
                valid_geom = Polygon(exterior, interiors)
                geometries.append(valid_geom)
            elif geom.geom_type == "MultiPolygon":
                valid_polygons = []
                for poly in geom.geoms:
                    exterior = poly.exterior.coords[:]
                    interiors = [interior.coords[:] for interior in poly.interiors]
                    if not is_counterclockwise(exterior):
                        exterior = list(reversed(exterior))
                    for i in range(len(interiors)):
                        if is_counterclockwise(interiors[i]):
                            interiors[i] = list(reversed(interiors[i]))
                    valid_polygons.append(Polygon(exterior, interiors))
                valid_geom = MultiPolygon(valid_polygons)
                geometries.append(valid_geom)
        else:
            raise ValueError(f"{path} 中未发现 Feature 或 FeatureCollection 类型")

        if not geometries:
            raise ValueError(f"{path} 中未发现 Polygon 或 MultiPolygon 几何")

        # 转换坐标系并计算总面积
        gseries = gpd.GeoSeries(geometries, crs="EPSG:4326").to_crs("EPSG:3857")
        total_area = gseries.area.sum()
        results[path] = total_area

    return results

def is_counterclockwise(coords: List[List[float]]) -> bool:
    """判断坐标列表是否为逆时针顺序（通过计算面积符号）"""
    # 简单多边形面积公式，若结果为正则是逆时针
    area = 0.5 * sum(
        (x1 * y2 - x2 * y1  for (x1, y1), (x2, y2) in zip(coords[:-1], coords[1:])
    ))
    return area > 0