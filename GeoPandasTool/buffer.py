import geopandas as gpd
import json
from shapely.geometry import shape
from shapely.geometry import mapping

def buffer(geojson_str, distance):
    """
    计算 Overpass API 获取的 GeoJSON 数据的缓冲区（buffer）。

    参数:
        geojson_str (str): GeoJSON 字符串
        distance (float): 缓冲区的距离（单位与坐标系一致）

    返回:
        str: 计算缓冲区后的 GeoJSON 字符串
    """
    # 解析 GeoJSON 数据
    geojson_data = json.loads(geojson_str)

    # 提取几何对象
    geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]]

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)

    # 计算缓冲区
    buffer_gseries = gseries.buffer(distance)

    # 生成新的 GeoJSON 结果
    buffer_features = []
    for geom in buffer_gseries:
        if not geom.is_empty:  # 仅保留非空对象
            buffer_features.append({
                "type": "Feature",
                "geometry": mapping(geom),
                "properties": {}  # 可根据需要添加属性
            })

    buffer_geojson = {
        "type": "FeatureCollection",
        "features": buffer_features
    }

    return json.dumps(buffer_geojson, indent=2)
