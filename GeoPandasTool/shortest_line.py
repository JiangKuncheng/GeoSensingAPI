import geopandas as gpd
import json
from shapely.geometry import shape

def shortest_line_between_two(geojson_str1, geojson_str2):
    """
    计算两个 GeoJSON 字符串中的地理对象之间的最短连接线。

    参数:
        geojson_str1 (str): 第一个 GeoJSON 字符串（包含一个几何对象）。
        geojson_str2 (str): 第二个 GeoJSON 字符串（包含一个几何对象）。

    返回:
        str: 表示最短连接线的 GeoJSON 字符串。
    """
    # 解析 GeoJSON 并提取第一个 geometry
    geojson_data1 = json.loads(geojson_str1)
    geom1 = shape(geojson_data1["features"][0]["geometry"])

    # 解析 GeoJSON 并提取第二个 geometry
    geojson_data2 = json.loads(geojson_str2)
    geom2 = shape(geojson_data2["features"][0]["geometry"])

    # 构建 GeoSeries
    g1 = gpd.GeoSeries([geom1])
    g2 = gpd.GeoSeries([geom2])

    # 计算最短连接线
    shortest_line = g1.shortest_line(g2)[0]

    # 构造 GeoJSON Feature
    feature = {
        "type": "Feature",
        "geometry": json.loads(shortest_line.to_json()),
        "properties": {}
    }

    # 构造 FeatureCollection 并转成 JSON 字符串
    result_geojson = {
        "type": "FeatureCollection",
        "features": [feature]
    }

    return json.dumps(result_geojson, indent=2)

