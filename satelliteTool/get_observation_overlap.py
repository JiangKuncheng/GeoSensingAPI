import json

from pyproj import Proj, Transformer
from shapely.geometry import shape
from shapely.ops import unary_union, transform
from shapely.validation import make_valid

# 导入您已经写好的函数
from satelliteTool.get_observation_lace import get_coverage_lace


def get_observation_overlap(
    tle_dict: dict,
    start_time_str: str,
    end_time_str: str,
    target_geojson: dict,
    fov: float = 10.0,
    interval_seconds: int = 300
) -> dict:
    """
    计算多个卫星在指定时间段内与目标区域的观测重叠面积比例，返回一个字典。

    :param tle_dict: 一个字典，键是卫星名称(str)，值是两行的TLE字符串(str)。
    :param start_time_str: 观测开始时间的字符串 (例如 "2025-08-01 00:00:00.000")。
    :param end_time_str: 观测结束时间的字符串 (例如 "2025-08-01 23:59:59.000")。
    :param target_geojson: 目标区域的GeoJSON格式数据。
    :param fov: 卫星的视场角 (Field of View)，单位是度。默认为 10.0。
    :param interval_seconds: 计算轨迹点的时间间隔，单位是秒。默认为 300 (5分钟)。
    :return: 一个字典，键是卫星名称，值是覆盖率（重叠比例），只包含重叠比例大于零的卫星。
    """
    # 使用您已经写好的函数获取卫星覆盖轨迹
    coverage_geojson = get_coverage_lace(
        tle_dict=tle_dict,
        start_time_str=start_time_str,
        end_time_str=end_time_str,
        fov=fov,
        interval_seconds=interval_seconds
    )
    
    # 解析目标区域
    target_polygon = shape(target_geojson["features"][0]["geometry"])
    
    # 定义坐标转换器（等面积投影用于计算面积）
    wgs84_proj = Proj('epsg:4326')
    equal_area_proj = Proj('+proj=moll')  # Mollweide 等面积投影
    to_aea_transformer = Transformer.from_proj(wgs84_proj, equal_area_proj, always_xy=True)
    
    # 转换并计算目标面积
    projected_target_geom = transform(to_aea_transformer.transform, target_polygon)
    target_area = projected_target_geom.area
    
    if target_area == 0:
        return {}
    
    # 按卫星分组处理覆盖轨迹
    satellite_coverage = {}
    for feature in coverage_geojson['features']:
        # 检查几何数据是否为空
        if feature['geometry'] is None:
            continue
            
        satellite_name = feature['properties']['satellite']
        if satellite_name not in satellite_coverage:
            satellite_coverage[satellite_name] = []
        
        try:
            geom = shape(feature['geometry'])
            # 检查几何图形是否有效
            if geom.is_valid and not geom.is_empty:
                satellite_coverage[satellite_name].append(geom)
        except Exception as e:
            print(f"跳过无效的几何图形: {e}")
            continue
    
    # 计算每个卫星的重叠比例
    overlap_results = {}
    
    for satellite_name, footprint_polygons in satellite_coverage.items():
        if not footprint_polygons:
            continue
            
        try:
            # 合并该卫星的所有足迹
            if len(footprint_polygons) == 1:
                total_coverage = footprint_polygons[0]
            else:
                # 处理跨越日期变更线的情况
                valid_polygons = []
                for poly in footprint_polygons:
                    try:
                        # 尝试修复几何图形
                        if not poly.is_valid:
                            poly = make_valid(poly)
                        if poly.is_valid and not poly.is_empty:
                            valid_polygons.append(poly)
                    except Exception:
                        continue
                
                if not valid_polygons:
                    continue
                    
                try:
                    total_coverage = unary_union(valid_polygons)
                except Exception as e:
                    print(f"合并 {satellite_name} 的足迹时出错: {e}")
                    continue
            
            if total_coverage.is_empty:
                continue
                
            # 计算与目标区域的交集
            try:
                intersection = total_coverage.intersection(target_polygon)
            except Exception as e:
                print(f"计算 {satellite_name} 的交集时出错: {e}")
                continue
                
            if intersection.is_empty:
                continue
                
            # 转换到等面积投影并计算面积
            try:
                projected_intersection = transform(to_aea_transformer.transform, intersection)
                intersection_area = projected_intersection.area
            except Exception as e:
                print(f"投影 {satellite_name} 的交集时出错: {e}")
                continue
            
            # 计算覆盖率
            coverage_ratio = intersection_area / target_area
            
            # 只保留覆盖率大于零的卫星
            if coverage_ratio > 0:
                overlap_results[satellite_name] = coverage_ratio
                
        except Exception as e:
            print(f"处理卫星 {satellite_name} 时出错: {str(e)}")
            continue
    
    return overlap_results


if __name__ == '__main__':
    # --- 示例数据 ---
    tle_data_dict = {
        "LANDSAT 9": "1 49260U 21088A   25225.90087331  .00000343  00000-0  86120-4 0  9998\n2 49260  98.2240 295.6621 0001152  92.7233 267.4097 14.57102349206250",
        "LANDSAT 8": "1 39084U 13008A   25225.93518726  .00000330  00000-0  83304-4 0  9991\n2 39084  98.2219 295.6904 0001221  90.8808 269.2530 14.57106224653150",
        "LANDSAT 7": "1 25682U 99020A   25225.96558631  .00000447  00000-0  94797-4 0  9997\n2 25682  97.8629 238.7471 0001408  78.5884 338.4838 14.63487946400903",
        "SENTINEL 2A": "1 40697U 15028A   25225.66220237  .00000108  00000-0  57680-4 0  9995\n2 40697  98.5664 299.9242 0001176  96.3963 263.7354 14.30826489529757",
        "SENTINEL 2B": "1 42063U 17013A   25225.93481032  .00000105  00000-0  56678-4 0  9995\n2 42063  98.5667 300.1355 0001261  95.8035 264.3292 14.30816795440702",
        "GAOFEN 6": "1 43484U 18048A   25225.89293148  .00000671  00000-0  10323-3 0  9990\n2 43484  97.8191 294.0983 0013707  87.9596 272.3184 14.76540806388048",
        "GAOFEN 1": "1 39150U 13018A   25225.93920346  .00000655  00000-0  10102-3 0  9996\n2 39150  97.9464 298.6386 0017702 171.2539 188.8983 14.76544463662908",
        "GAOFEN 1-02": "1 43259U 18031A   25225.89168981  .00000725  00000-0  11078-3 0  9996\n2 43259  97.7680 284.7617 0003750 264.3203  95.7580 14.76606704397354",
        "GAOFEN 1-03": "1 43260U 18031B   25225.93764942  .00000729  00000-0  11133-3 0  9998\n2 43260  97.7673 284.6950 0004656 311.5203  48.5607 14.76597261397351",
        "GAOFEN 1-04": "1 43262U 18031D   25225.91328914  .00000762  00000-0  11606-3 0  9995\n2 43262  97.7683 284.8258 0000988 345.8113  14.3069 14.76592202397343",
        "ZY-1 02E": "1 50465U 21131A   25225.87772090  .00000088  00000-0  45734-4 0  9997\n2 50465  98.4746 304.0172 0000690  26.8277 333.2944 14.35385677190337",
        "ZY-1 02D": "1 44528U 19059A   25225.87992434  .00000114  00000-0  54421-4 0  9995\n2 44528  98.3636 292.5392 0001232  21.9608 338.1630 14.35428680310252",
        "HJ-2F": "1 57519U 23116A   25225.95114683  .00009067  00000-0  38847-3 0  9998\n2 57519  97.3875 231.8057 0003349  45.7676 314.3835 15.22989263112039",
        "HJ-2E": "1 54035U 22132A   25225.91830765  .00009062  00000-0  38767-3 0  9993\n2 54035  97.3819 231.1366 0006806  21.0137 339.1378 15.23025509157696",
        "HJ-2B": "1 46479U 20067B   25225.94525504  .00000704  00000-0  10824-3 0  9994\n2 46479  97.9164 306.9150 0000744  73.7489 286.3803 14.76529418262923",
        "HJ-2A": "1 46478U 20067A   25225.90911622  .00000719  00000-0  11039-3 0  9994\n2 46478  97.9112 306.0764 0003417 141.3878 218.7377 14.76528696262914"
    }

    wuhan_target_str = """
    {"type":"FeatureCollection","features":[{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[114.0,30.0],[114.8,30.0],[114.8,30.8],[114.0,30.8],[114.0,30.0]]]}}]}
    """
    wuhan_target = json.loads(wuhan_target_str)

    # --- 调用函数并获取结果 ---
    print("--- 正在计算卫星观测重叠比例 ---")
    print(f"目标区域: 武汉地区")
    print(f"卫星数量: {len(tle_data_dict)}")
    print(f"时间范围: 2025-08-01 00:00:00.000 to 2025-08-01 23:59:59.000")
    
    overlap_results = get_observation_overlap(
        tle_dict=tle_data_dict,
        start_time_str="2025-08-01 00:00:00.000",
        end_time_str="2025-08-01 23:59:59.000",
        target_geojson=wuhan_target,
        fov=10.0,
        interval_seconds=600
    )
    
    print(f"\n--- 计算结果 ---")
    if overlap_results:
        for satellite, coverage in overlap_results.items():
            print(f"  - {satellite}: {coverage:.2%}")
    else:
        print("  没有卫星在该时间段内覆盖目标区域")
    
    print(f"\n返回的字典: {overlap_results}")