import geopandas as gpd
import json
from shapely.geometry import shape
from shapely.geometry import mapping

def translate(geojson_str, xoff=0.0, yoff=0.0):
    """
    平移 Overpass API 获取的 GeoJSON 数据中的几何对象。

    参数:
        geojson_str (str): GeoJSON 字符串。
        xoff (float): x 方向的偏移量（默认 0.0）。
        yoff (float): y 方向的偏移量（默认 0.0）。

    返回:
        str: 平移后的 GeoJSON 字符串。
    """
    # 解析 GeoJSON 数据
    geojson_data = json.loads(geojson_str)

    # 提取几何对象
    geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]]

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)

    # 进行几何平移
    translated_geometries = gseries.translate(xoff=xoff, yoff=yoff)

    # 生成新的 GeoJSON 结果
    translated_features = []
    for geom in translated_geometries:
        if not geom.is_empty:  # 仅保留非空对象
            translated_features.append({
                "type": "Feature",
                "geometry": mapping(geom),
                "properties": {}  # 可根据需要添加属性
            })

    translated_geojson = {
        "type": "FeatureCollection",
        "features": translated_features
    }

    return json.dumps(translated_geojson, indent=2)
