from shapely.geometry import shape, mapping
import geojson

from satelliteTool.getPlaceBoundary import get_boundary
def GisUnion(geojson1, geojson2):
    # 解析GeoJSON数据为Shapely对象
    polygon1 = shape(geojson1['features'][0]['geometry'])
    polygon2 = shape(geojson2['features'][0]['geometry'])

    # 计算并集
    union_polygon = polygon1.union(polygon2)

    # 转换回GeoJSON格式
    union_geojson = geojson.FeatureCollection([geojson.Feature(geometry=mapping(union_polygon))])

    return union_geojson


if __name__ == '__main__':
    area1=get_boundary("Hongshan District")
    area2=get_boundary("Hanyang District")
    area3=GisUnion(area1,area2)
    print(area3)