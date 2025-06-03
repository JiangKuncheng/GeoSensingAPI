from shapely.geometry import shape, mapping
import geojson

from satelliteTool.getPlaceBoundary import get_boundary


def GisDefference(geojson1, geojson2):
    # 解析GeoJSON数据为Shapely对象
    polygon1 = shape(geojson1['features'][0]['geometry'])
    polygon2 = shape(geojson2['features'][0]['geometry'])

    # 计算差集（polygon1 减去 polygon2）
    difference_polygon = polygon1.difference(polygon2)

    # 转换回GeoJSON格式
    difference_geojson = geojson.FeatureCollection([geojson.Feature(geometry=mapping(difference_polygon))])

    return difference_geojson

if __name__ == '__main__':
    area1=get_boundary("Wuhan")
    area2=get_boundary("Hanyang District")
    area3=GisDefference(area1,area2)
    print(area3)