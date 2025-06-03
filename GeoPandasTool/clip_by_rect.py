import geopandas as gpd
import json
from shapely.geometry import shape

def clip_by_rect(geojson_str, xmin, ymin, xmax, ymax):
    """
    裁剪 Overpass API 获取的 GeoJSON 数据，使其仅保留指定矩形区域内的部分。

    参数:
        geojson_str (str): 需要裁剪的 GeoJSON 字符串
        xmin (float): 矩形裁剪框的最小 x 坐标（左边界）
        ymin (float): 矩形裁剪框的最小 y 坐标（下边界）
        xmax (float): 矩形裁剪框的最大 x 坐标（右边界）
        ymax (float): 矩形裁剪框的最大 y 坐标（上边界）

    返回:
        str: 裁剪后的 GeoJSON 字符串
    """
    # 解析 GeoJSON
    geojson = json.loads(geojson_str)

    # 提取几何对象
    geometries = [shape(feature["geometry"]) for feature in geojson["features"]]

    # 构建 GeoSeries 并进行裁剪
    gseries = gpd.GeoSeries(geometries)
    clipped_gseries = gseries.clip_by_rect(xmin, ymin, xmax, ymax)

    # 生成新的 GeoJSON 结果
    clipped_features = []
    for i, geom in enumerate(clipped_gseries):
        if not geom.is_empty:  # 仅保留裁剪后仍有数据的对象
            clipped_features.append({
                "type": "Feature",
                "geometry": json.loads(geom.to_json()),
                "properties": geojson["features"][i].get("properties", {})  # 保留原始属性
            })

    clipped_geojson = {
        "type": "FeatureCollection",
        "features": clipped_features
    }

    return json.dumps(clipped_geojson, indent=2)
