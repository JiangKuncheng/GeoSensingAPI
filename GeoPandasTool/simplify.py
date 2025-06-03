import geopandas as gpd
import json
from shapely.geometry import shape

def simplify(geojson_str, tolerance=0.01, preserve_topology=True):
    """
    简化 Overpass API 获取的 GeoJSON 数据中的几何对象。

    参数:
        geojson_str (str): GeoJSON 字符串。
        tolerance (float): 简化程度，值越大简化越明显。
        preserve_topology (bool): 是否保持拓扑结构。

    返回:
        str: 简化后的 GeoJSON 字符串。
    """
    # 解析 GeoJSON 数据
    geojson_data = json.loads(geojson_str)

    # 提取几何对象
    geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]]

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)

    # 进行几何简化
    simplified_geometries = gseries.simplify(tolerance, preserve_topology=preserve_topology)

    # 生成新的 GeoJSON 结果
    simplified_features = []
    for geom in simplified_geometries:
        if not geom.is_empty:  # 仅保留非空对象
            simplified_features.append({
                "type": "Feature",
                "geometry": json.loads(geom.to_json()),
                "properties": {}  # 可根据需要添加属性
            })

    simplified_geojson = {
        "type": "FeatureCollection",
        "features": simplified_features
    }

    return json.dumps(simplified_geojson, indent=2)
