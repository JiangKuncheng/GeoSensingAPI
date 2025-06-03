import json
from shapely.geometry import shape, Polygon


def has_intersection(json1: str, json2: str) -> str:
    """
    判断两个Overpass API返回的JSON数据是否在几何拓扑上有交集。
    :param json1: 第一个Overpass API的JSON字符串
    :param json2: 第二个Overpass API的JSON字符串
    :return: 有交集返回 "True"，否则返回 "False"
    """
    try:
        data1 = json.loads(json1)
        data2 = json.loads(json2)

        polygons1 = [shape(element["geometry"]) for element in data1.get("elements", []) if
                     "geometry" in element and isinstance(shape(element["geometry"]), Polygon)]
        polygons2 = [shape(element["geometry"]) for element in data2.get("elements", []) if
                     "geometry" in element and isinstance(shape(element["geometry"]), Polygon)]

        for poly1 in polygons1:
            for poly2 in polygons2:
                if poly1.intersects(poly2):  # 进行几何拓扑上的交集判断
                    return "True"

        return "False"
    except Exception as e:
        return f"Error: {str(e)}"
