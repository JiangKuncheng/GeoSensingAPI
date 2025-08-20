import json

from pyproj import Proj, Transformer
from shapely.geometry import shape, Polygon, MultiPolygon
from shapely.ops import unary_union, transform
from shapely.validation import make_valid
from shapely.geometry import mapping

# 导入您已经写好的函数
from satelliteTool.get_observation_lace import get_coverage_lace


def split_antimeridian(geom):
    """
    分割跨越180度经线（国际日期变更线）的几何图形。

    :param geom: Shapely几何图形对象。
    :return: 原始几何图形或被分割后的MultiPolygon。
    """
    if not isinstance(geom, Polygon) or geom.bounds[2] - geom.bounds[0] < 180:
        return geom

    cutter = Polygon([(-180, -90), (-180, 90), (0, 90), (0, -90), (-180, -90)])
    parts = []
    intersected = geom.intersection(cutter)
    if not intersected.is_empty:
        parts.append(intersected)

    diffed = geom.difference(cutter)
    if not diffed.is_empty:
        shifted_part = transform(lambda x, y, z=None: (x - 360, y), diffed)
        parts.append(shifted_part)

    return MultiPolygon(parts)


# ==============================================================================
# 函数 3: 主函数 - 计算重叠率 (已优化，更高效)
# ==============================================================================
def get_observation_overlap(
        tle_dict: dict,
        start_time_str: str,
        end_time_str: str,
        target_geojson: dict,
        fov: float = 10.0,
        interval_seconds: int = 300
) -> dict:
    """
    使用高效、健壮的方法计算卫星观测与目标区域的重叠率。

    策略: 逐一计算每个小足迹与目标区的交集，最后合并这些小交集。
          这避免了生成巨大的全局覆盖多边形，从而大大提高了性能和稳定性。
    """
    # 1. 调用函数获取所有卫星的覆盖足迹
    coverage_dict = get_coverage_lace(
        tle_dict=tle_dict,
        start_time_str=start_time_str,
        end_time_str=end_time_str,
        fov=fov,
        interval_seconds=interval_seconds
    )

    # 2. 准备目标区域和坐标投影
    try:
        target_polygon = shape(target_geojson["features"][0]["geometry"])
        if not target_polygon.is_valid:
            target_polygon = make_valid(target_polygon)
    except (IndexError, KeyError):
        print("错误: 无效的目标区域GeoJSON格式。")
        return {}

    wgs84_proj = Proj('epsg:4326')
    equal_area_proj = Proj('+proj=moll')  # Mollweide 等面积投影
    to_aea_transformer = Transformer.from_proj(wgs84_proj, equal_area_proj, always_xy=True).transform

    projected_target_geom = transform(to_aea_transformer, target_polygon)
    target_area = projected_target_geom.area

    if target_area == 0:
        return {}

    # 3. 逐个卫星进行处理
    overlap_results = {}
    for satellite_name, satellite_geojson in coverage_dict.items():
        if not satellite_geojson.get('features'):
            continue

        intersections = []
        intersecting_footprints_features = []

        # 4. 高效策略：对每个足迹单独求交集
        for feature in satellite_geojson['features']:
            if not feature.get('geometry'):
                continue

            try:
                footprint_geom = shape(feature['geometry'])

                if not footprint_geom.is_valid:
                    footprint_geom = make_valid(footprint_geom)

                footprint_geom = split_antimeridian(footprint_geom)

                if footprint_geom.is_empty:
                    continue

                # 核心：计算单个足迹与目标区域的交集
                intersection = footprint_geom.intersection(target_polygon)

                if not intersection.is_empty:
                    intersections.append(intersection)

                    intersection_feature = {
                        'type': 'Feature',
                        'geometry': mapping(intersection),
                        'properties': {
                            'satellite': satellite_name,
                            'timestamp': feature['properties']['timestamp'],
                        }
                    }
                    intersecting_footprints_features.append(intersection_feature)

            except Exception as e:
                print(f"跳过卫星 {satellite_name} 的一个足迹，原因: {e}")
                continue

        # 5. 合并所有小的交集，并计算总面积
        if intersections:
            total_intersection_geom = unary_union(intersections)

            projected_intersection = transform(to_aea_transformer, total_intersection_geom)
            intersection_area = projected_intersection.area

            coverage_ratio = min(1.0, intersection_area / target_area)

            if coverage_ratio > 0:
                overlap_results[satellite_name] = {
                    'coverage_ratio': coverage_ratio,
                    'intersection_footprints': intersecting_footprints_features
                }

    return overlap_results


# ==============================================================================
# 示例运行部分
# ==============================================================================
if __name__ == '__main__':
    # --- 1. 定义卫星TLE数据 ---
    # 这里我们使用几个有代表性的卫星进行测试
    tle_data_dict = {
        "GAOFEN 1-03": "1 43260U 18031B   25225.93764942  .00000729  00000-0  11133-3 0  9998\n2 43260  97.7673 284.6950 0004656 311.5203  48.5607 14.76597261397351",
        "SENTINEL 2A": "1 40697U 15028A   25225.66220237  .00000108  00000-0  57680-4 0  9995\n2 40697  98.5664 299.9242 0001176  96.3963 263.7354 14.30826489529757",
        "LANDSAT 9": "1 49260U 21088A   25225.90087331  .00000343  00000-0  86120-4 0  9998\n2 49260  98.2240 295.6621 0001152  92.7233 267.4097 14.57102349206250",
    }

    # --- 2. 定义目标区域 (武汉) ---
    wuhan_target_str = """
    {"type":"FeatureCollection","features":[{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[114.0,30.0],[114.8,30.0],[114.8,30.8],[114.0,30.8],[114.0,30.0]]]}}]}
    """
    wuhan_target = json.loads(wuhan_target_str)

    # --- 3. 设置计算参数 ---
    start_time = "2025-08-01 00:00:00.000"
    end_time = "2025-08-01 23:59:59.000"
    field_of_view = 45.0
    time_interval = 600  # 10分钟

    # --- 4. 调用主函数并打印结果 ---
    print("--- 开始计算卫星观测重叠率 ---")

    overlap_results = get_observation_overlap(
        tle_dict=tle_data_dict,
        start_time_str=start_time,
        end_time_str=end_time,
        target_geojson=wuhan_target,
        fov=field_of_view,
        interval_seconds=time_interval
    )

    print("\n" + "=" * 50)
    print("--- 计算结果 ---")
    if overlap_results:
        for satellite, data in overlap_results.items():
            coverage = data['coverage_ratio']
            footprint_count = len(data['intersection_footprints'])
            print(f"  - 卫星: {satellite:<15} | 覆盖率: {coverage:>7.2%} | 相交足迹数: {footprint_count}")

        # --- 5. 将相交的足迹保存到文件以便验证 ---
        all_intersecting_features = []
        for data in overlap_results.values():
            all_intersecting_features.extend(data['intersection_footprints'])

        intersecting_geojson = {
            "type": "FeatureCollection",
            "features": all_intersecting_features
        }

        output_filename = 'intersecting_footprints.json'
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(intersecting_geojson, f, indent=2, ensure_ascii=False)
        print(f"\n✅ 所有相交足迹已保存到文件: {output_filename}")

    else:
        print("  在指定时间段内，没有卫星覆盖目标区域。")
    print("=" * 50)