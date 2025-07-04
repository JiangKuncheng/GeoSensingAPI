import geopandas as gpd
import json
from shapely.geometry import shape
from shapely.geometry import mapping

def remove_repeated_points(geojson_str):
    """
    移除 Overpass API 获取的 GeoJSON 数据中的重复点。

    参数:
        geojson_str (str): GeoJSON 字符串

    返回:
        str: 去除重复点后的 GeoJSON 字符串
    """
    # 解析 GeoJSON 数据
    geojson_data = json.loads(geojson_str)

    # 提取几何对象
    geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]]

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)

    # 移除重复点 - 对于Polygon和MultiPolygon，我们简化处理
    cleaned_geometries = []
    for geom in gseries:
        if geom.is_valid:
            # 对于有效的几何对象，尝试简化来移除重复点
            try:
                cleaned_geom = geom.simplify(0, preserve_topology=True)
                cleaned_geometries.append(cleaned_geom)
            except:
                cleaned_geometries.append(geom)
        else:
            cleaned_geometries.append(geom)

    # 生成新的 GeoJSON 结果
    cleaned_features = []
    for geom in cleaned_geometries:
        if not geom.is_empty:  # 仅保留非空对象
            cleaned_features.append({
                "type": "Feature",
                "geometry": mapping(geom),
                "properties": {}  # 可根据需要添加属性
            })

    cleaned_geojson = {
        "type": "FeatureCollection",
        "features": cleaned_features
    }

    return json.dumps(cleaned_geojson, indent=2)
