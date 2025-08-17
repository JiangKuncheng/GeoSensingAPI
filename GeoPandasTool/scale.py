import geopandas as gpd
import json
from shapely.geometry import shape
from shapely.geometry import mapping

def scale(geojson_str, xfact=1.0, yfact=1.0, origin="center"):
    """
    缩放 Overpass API 获取的 GeoJSON 数据中的几何对象。

    参数:
        geojson_str (str): GeoJSON 字符串。
        xfact (float): x 方向的缩放因子（默认为 1.0）。
        yfact (float): y 方向的缩放因子（默认为 1.0）。
        origin (str/tuple): 缩放中心，可选：
            - "center"（默认）：最小包围矩形的中心
            - "centroid"：几何质心
            - (x, y) 坐标点

    返回:
        str: 缩放后的 GeoJSON 字符串。
    """
    # 解析 GeoJSON 数据
    geojson_data = json.loads(geojson_str)

    # 提取几何对象
    geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]]

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)

    # 进行几何缩放
    scaled_geometries = gseries.scale(xfact=xfact, yfact=yfact, origin=origin)

    # 生成新的 GeoJSON 结果
    scaled_features = []
    for geom in scaled_geometries:
        if not geom.is_empty:  # 仅保留非空对象
            scaled_features.append({
                "type": "Feature",
                "geometry": mapping(geom),
                "properties": {}  # 可根据需要添加属性
            })

    scaled_geojson = {
        "type": "FeatureCollection",
        "features": scaled_features
    }

    return json.dumps(scaled_geojson, indent=2)
