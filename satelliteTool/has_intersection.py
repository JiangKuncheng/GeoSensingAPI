import json
from shapely.geometry import shape, Polygon


def has_intersection(json1: str, json2: str) -> str:
    """
    判断两个GeoJSON数据是否在几何拓扑上有交集。
    :param json1: 第一个GeoJSON字符串
    :param json2: 第二个GeoJSON字符串  
    :return: 有交集返回 "True"，否则返回 "False"
    """
    try:
        data1 = json.loads(json1)
        data2 = json.loads(json2)

        # 提取几何对象 - 支持标准GeoJSON格式
        def extract_geometries(data):
            geometries = []
            if data.get("type") == "FeatureCollection":
                for feature in data.get("features", []):
                    if "geometry" in feature:
                        geom = shape(feature["geometry"])
                        geometries.append(geom)
            elif data.get("type") == "Feature":
                if "geometry" in data:
                    geom = shape(data["geometry"])
                    geometries.append(geom)
            # 兼容Overpass API格式
            elif "elements" in data:
                for element in data.get("elements", []):
                    if "geometry" in element:
                        geom = shape(element["geometry"])
                        geometries.append(geom)
            return geometries

        geometries1 = extract_geometries(data1)
        geometries2 = extract_geometries(data2)

        # 检查交集
        for geom1 in geometries1:
            for geom2 in geometries2:
                if geom1.intersects(geom2):  # 进行几何拓扑上的交集判断
                    return "True"

        return "False"
    except Exception as e:
        return f"Error: {str(e)}"
