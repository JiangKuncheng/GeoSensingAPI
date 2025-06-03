from shapely.geometry import shape, mapping
import geojson

from satelliteTool.getPlaceBoundary import get_boundary


def GisInsection(geojson1, geojson2):
    # 解析GeoJSON数据为Shapely对象
    polygon1 = shape(geojson1['features'][0]['geometry'])
    polygon2 = shape(geojson2['features'][0]['geometry'])

    # 计算交集
    intersection_polygon = polygon1.intersection(polygon2)

    # 转换回GeoJSON格式
    intersection_geojson = geojson.FeatureCollection([geojson.Feature(geometry=mapping(intersection_polygon))])

    return intersection_geojson


if __name__ == '__main__':
    area1=get_boundary("Wuhan")
    area2=get_boundary("Hanyang District")
    area3=GisInsection(area1,area2)
    print(area3)