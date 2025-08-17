import geopandas as gpd
import json
from shapely.geometry import shape
from shapely.geometry import mapping

def rotate(geojson_str, angle, origin='centroid', use_radians=False):
    """
    旋转 Overpass API 获取的 GeoJSON 数据中的几何对象。

    参数:
        geojson_str (str): GeoJSON 字符串。
        angle (float): 旋转角度（默认为度，use_radians=True 时为弧度）。
        origin (str/tuple): 旋转中心，可为 'centroid'、'center' 或指定坐标 (x, y)。
        use_radians (bool): 是否使用弧度进行旋转（默认为 False）。

    返回:
        str: 旋转后的 GeoJSON 字符串。
    """
    # 解析 GeoJSON 数据
    geojson_data = json.loads(geojson_str)

    # 提取几何对象
    geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]]

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)

    # 进行几何旋转
    rotated_geometries = gseries.rotate(angle, origin=origin, use_radians=use_radians)

    # 生成新的 GeoJSON 结果
    rotated_features = []
    for geom in rotated_geometries:
        if not geom.is_empty:  # 仅保留非空对象
            rotated_features.append({
                "type": "Feature",
                "geometry": mapping(geom),
                "properties": {}  # 可根据需要添加属性
            })

    rotated_geojson = {
        "type": "FeatureCollection",
        "features": rotated_features
    }

    return json.dumps(rotated_geojson, indent=2)
