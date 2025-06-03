import geopandas as gpd
import json
from shapely.geometry import shape

def reverse(geojson_str):
    """
    反转 Overpass API 获取的 GeoJSON 数据中的几何对象的坐标顺序。

    参数:
        geojson_str (str): GeoJSON 字符串。

    返回:
        str: 反转坐标后的 GeoJSON 字符串。
    """
    # 解析 GeoJSON 数据
    geojson_data = json.loads(geojson_str)

    # 提取几何对象
    geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]]

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)

    # 反转几何对象的坐标顺序
    reversed_geometries = gseries.apply(lambda x: x.reverse() if x.is_valid else x)

    # 生成新的 GeoJSON 结果
    reversed_features = []
    for geom in reversed_geometries:
        if not geom.is_empty:  # 仅保留非空对象
            reversed_features.append({
                "type": "Feature",
                "geometry": json.loads(geom.to_json()),
                "properties": {}  # 可根据需要添加属性
            })

    reversed_geojson = {
        "type": "FeatureCollection",
        "features": reversed_features
    }

    return json.dumps(reversed_geojson, indent=2)
