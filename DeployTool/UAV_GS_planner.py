# -*- coding: utf-8 -*-
"""
PROJECT_NAME: Other_Python
FILE_NAME: UAV_GS_planner
AUTHOR: welt
E_MAIL: tjlwelt@foxmail.com
DATE: 2025-08-13
"""

import os
import math
import sys
import json
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, LineString, Point, MultiPoint, MultiLineString
from shapely.ops import unary_union, voronoi_diagram
from sklearn.cluster import KMeans
import numpy as np
import folium
import matplotlib.pyplot as plt


# ==============================================================================
# 1. 辅助函数 (Helper Functions)
# ==============================================================================
def create_wuhan_geojson(file_path="wuhan_east_lake.geojson"):
    if os.path.exists(file_path):
        print(f"文件 '{file_path}' 已存在，将使用现有文件。")
        return
    print(f"正在创建虚拟GeoJSON文件: '{file_path}'")
    polygon_geom = Polygon([
        (114.3948, 30.5488), (114.4102, 30.5594), (114.4208, 30.5458),
        (114.4033, 30.5365), (114.3948, 30.5488)
    ])
    gdf = gpd.GeoDataFrame(geometry=[polygon_geom], crs="EPSG:4326")
    gdf.to_file(file_path, driver='GeoJSON')
    print("虚拟GeoJSON文件创建成功。")


def get_utm_crs(gdf_latlon):
    centroid = gdf_latlon.unary_union.centroid
    lon, lat = centroid.x, centroid.y
    utm_band = str(int((lon + 180) // 6 + 1))
    if lat >= 0:
        epsg_code = '326' + utm_band.zfill(2)
    else:
        epsg_code = '327' + utm_band.zfill(2)
    return f"EPSG:{epsg_code}"


# ==============================================================================
# 2. 核心路径生成函数 (已完全重构)
# ==============================================================================
def generate_s_path_in_polygon(polygon: (Polygon, MultiPolygon), swath_width: float) -> (object, float):
    """
    【已重构】为一个或多个可能带有空洞的多边形生成S形扫描路径。
    此函数现在能够正确处理复杂形状，通过生成一个MultiLineString来避免穿越禁飞区。

    :param polygon: 一个Polygon或MultiPolygon对象，代表无人机的有效飞行区域。
    :param swath_width: 无人机的扫描幅宽。
    :return: 一个包含所有有效路径段的MultiLineString对象和总路径长度。
    """
    if polygon.is_empty or polygon.area == 0:
        return None, 0

    # 【优化】如果输入是MultiPolygon，递归地为每个部分规划路径并合并结果
    if isinstance(polygon, MultiPolygon):
        all_path_segments = []
        total_length = 0
        for p in polygon.geoms:
            path, length = generate_s_path_in_polygon(p, swath_width)  # 递归调用
            if path:
                all_path_segments.extend(list(path.geoms))
                total_length += length
        if not all_path_segments:
            return None, 0
        return MultiLineString(all_path_segments), total_length

    # --- 以下是针对单个Polygon（可能带孔）的核心逻辑 ---
    mbr = polygon.minimum_rotated_rectangle
    if mbr.is_empty:
        return None, 0

    # 计算旋转角度以使MBR的长边与X轴平行
    x, y = mbr.exterior.coords.xy
    edge_lengths = (Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
    long_edge_start_pt = (Point(x[0], y[0]), Point(x[1], y[1])) if edge_lengths[0] > edge_lengths[1] else (
        Point(x[1], y[1]), Point(x[2], y[2]))
    angle_rad = math.atan2(long_edge_start_pt[1].y - long_edge_start_pt[0].y,
                           long_edge_start_pt[1].x - long_edge_start_pt[0].x)

    rotated_poly = gpd.GeoSeries(polygon).rotate(-math.degrees(angle_rad), origin=(0, 0)).iloc[0]
    min_x, min_y, max_x, max_y = rotated_poly.bounds

    scan_segments = []
    y_current = min_y + swath_width / 2
    direction = 1  # 1表示从左到右, -1表示从右到左

    while y_current <= max_y:
        scan_line = LineString([(min_x - 1, y_current), (max_x + 1, y_current)])
        intersected = rotated_poly.intersection(scan_line)

        if not intersected.is_empty:
            # 标准化处理，确保我们总是在处理一个几何体列表
            geoms = list(intersected.geoms) if intersected.geom_type == 'MultiLineString' else [intersected]
            # 始终按X坐标对分段进行排序
            geoms.sort(key=lambda g: g.coords[0][0])
            # 【优化】如果扫描方向是反向的，则反转整个段列表的顺序
            if direction == -1:
                geoms.reverse()
            scan_segments.extend(geoms)

        y_current += swath_width
        direction *= -1

    if not scan_segments:
        return None, 0

    # 【核心变更】将所有独立的路径段组合成一个MultiLineString，而不是试图连接它们
    final_path_rotated = MultiLineString(scan_segments)
    final_path = gpd.GeoSeries(final_path_rotated).rotate(math.degrees(angle_rad), origin=(0, 0)).iloc[0]

    # 确保返回类型一致
    if final_path.geom_type == 'LineString':
        final_path = MultiLineString([final_path])

    return final_path, final_path.length


# ==============================================================================
# 3. 主规划器类 (Main Planner Class) - 无需修改
# ==============================================================================
class CollaborativePlanner:
    def __init__(self, geojson_path: str, uavs_params: list, ground_station_params: dict = None):
        print("--- 初始化空地协同规划器 ---")
        self.uavs = uavs_params
        self.num_uavs = len(uavs_params)
        self.ground_station = ground_station_params

        print(f"加载区域文件: {geojson_path}")
        self.area_gdf_latlon = gpd.read_file(geojson_path).to_crs("EPSG:4326")
        self.original_crs = self.area_gdf_latlon.crs
        self.utm_crs = get_utm_crs(self.area_gdf_latlon)
        print(f"原始坐标系: {self.original_crs}. 内部计算将使用UTM坐标系: {self.utm_crs}")

        self.area_gdf_utm = self.area_gdf_latlon.to_crs(self.utm_crs)
        self.total_area_shape_utm = self.area_gdf_utm.unary_union

        self.ground_station_coverage_utm = None
        self._initialize_ground_station()

        if self.ground_station_coverage_utm:
            self.uav_target_area_utm = self.total_area_shape_utm.difference(self.ground_station_coverage_utm)
            print("已扣除地面站覆盖范围，无人机将规划剩余区域。")
        else:
            self.uav_target_area_utm = self.total_area_shape_utm

        self.results = []
        self.coverage_percentage = 0.0

    def _initialize_ground_station(self):
        if not self.ground_station:
            print("未提供地面站信息。")
            return
        print("正在处理地面站信息...")
        try:
            gs_latlon = Point(self.ground_station['coords_latlon'])
            gs_radius_m = self.ground_station['observation_radius_m']
            gs_utm = gpd.GeoSeries([gs_latlon], crs=self.original_crs).to_crs(self.utm_crs).iloc[0]
            self.ground_station_coverage_utm = gs_utm.buffer(gs_radius_m)
            self.ground_station['geom_utm'] = gs_utm
            print(f"地面站覆盖区（半径 {gs_radius_m}m）创建成功。")
        except (KeyError, IndexError) as e:
            print(f"【错误】地面站参数格式不正确。错误详情: {e}")
            self.ground_station = None

    def pre_check_feasibility(self):
        print("\n--- 执行可行性预检查 ---")
        uav_area_needed = self.uav_target_area_utm.area
        total_max_coverage_capability = sum(
            uav['speed'] * uav['flight_time'] * uav['swath_width'] for uav in self.uavs
        )
        print(f"总任务区域面积: {self.total_area_shape_utm.area:.2f} m²")
        if self.ground_station_coverage_utm:
            gs_cover_in_area = self.total_area_shape_utm.intersection(self.ground_station_coverage_utm).area
            print(f"地面站已覆盖面积: {gs_cover_in_area:.2f} m²")
        print(f"无人机需覆盖的剩余面积: {uav_area_needed:.2f} m²")
        print(f"无人机队理论最大总覆盖能力: {total_max_coverage_capability:.2f} m²")
        if total_max_coverage_capability < uav_area_needed:
            print("【警告】无法覆盖该区域：机队总覆盖能力小于剩余的区域面积需求。")
            return False
        else:
            print("【成功】预检查通过，机队理论上有能力覆盖剩余区域。")
            return True

    def decompose_area_and_assign(self, n_points_per_sq_km=5):
        print(f"\n--- 步骤 1: 使用K-Means和泰森多边形分解无人机目标区域 ---")
        if self.uav_target_area_utm.is_empty:
            print("无人机目标区域为空，无需分解。")
            self.results = [{"uav_id": uav['id'], "uav_params": uav, "sub_area_utm": Polygon()} for uav in self.uavs]
            return
        area_sq_km = self.uav_target_area_utm.area / 1_000_000
        n_points = max(self.num_uavs * 50, int(area_sq_km * n_points_per_sq_km))
        min_x, min_y, max_x, max_y = self.uav_target_area_utm.bounds
        points_inside = []
        while len(points_inside) < n_points:
            rand_points = np.random.rand(n_points * 2, 2)
            rand_points[:, 0] = rand_points[:, 0] * (max_x - min_x) + min_x
            rand_points[:, 1] = rand_points[:, 1] * (max_y - min_y) + min_y
            for p in rand_points:
                if len(points_inside) >= n_points: break
                if self.uav_target_area_utm.contains(Point(p)):
                    points_inside.append(p)
        points_arr = np.array(points_inside)
        kmeans = KMeans(n_clusters=self.num_uavs, random_state=42, n_init=10).fit(points_arr)
        centers = MultiPoint(kmeans.cluster_centers_)
        voronoi_cells = voronoi_diagram(centers, envelope=self.uav_target_area_utm)
        print(f"已生成 {len(voronoi_cells.geoms)} 个泰森多边形单元格。")
        self.results = []
        for i, center_point in enumerate(centers.geoms):
            uav = self.uavs[i]
            assigned_cell = None
            for cell in voronoi_cells.geoms:
                if cell.contains(center_point):
                    assigned_cell = cell
                    break
            sub_area_utm = self.uav_target_area_utm.intersection(assigned_cell) if assigned_cell else Polygon()
            self.results.append({"uav_id": uav['id'], "uav_params": uav, "sub_area_utm": sub_area_utm})
        print("无人机区域分解与分配完成。")

    def plan_paths_for_all(self):
        print("\n--- 步骤 2: 为每个无人机子区域规划路径 ---")
        for result in self.results:
            uav = result['uav_params']
            sub_area_utm = result['sub_area_utm']
            if sub_area_utm.is_empty:
                print(f"  - 无人机 {uav['id']} 分配区域为空，跳过。")
                result.update({'path_utm': None, 'path_length': 0, 'flight_duration_needed': 0, 'is_feasible': True})
                continue
            print(f"正在为无人机 {uav['id']} 规划路径...")
            path_utm, path_length = generate_s_path_in_polygon(sub_area_utm, uav['swath_width'])
            result['path_utm'] = path_utm
            result['path_length'] = path_length or 0
            if path_length and uav['speed'] > 0:
                duration = path_length / uav['speed']
                result['flight_duration_needed'] = duration
                result['is_feasible'] = duration <= uav['flight_time']
            else:
                result['flight_duration_needed'] = 0
                result['is_feasible'] = True

    def calculate_coverage(self):
        print("\n--- 步骤 3: 计算最终协同覆盖率 ---")
        all_coverage_polygons_utm = []
        for result in self.results:
            if result.get('path_utm') and not result['path_utm'].is_empty:
                uav = result['uav_params']
                coverage_poly_utm = result['path_utm'].buffer(uav['swath_width'] / 2, cap_style=2)
                all_coverage_polygons_utm.append(coverage_poly_utm)
        if self.ground_station_coverage_utm:
            all_coverage_polygons_utm.append(self.ground_station_coverage_utm)
        if not all_coverage_polygons_utm:
            self.coverage_percentage = 0.0
            return
        total_coverage_union_utm = unary_union(all_coverage_polygons_utm)
        effective_coverage_utm = self.total_area_shape_utm.intersection(total_coverage_union_utm)
        self.coverage_percentage = (effective_coverage_utm.area / self.total_area_shape_utm.area) * 100
        print(f"原始区域总面积: {self.total_area_shape_utm.area:.2f} m²")
        print(f"协同有效覆盖总面积: {effective_coverage_utm.area:.2f} m²")
        print(f"最终协同覆盖率: {self.coverage_percentage:.2f}%")

    def visualize_plan(self, output_file="collaborative_coverage_map.html"):
        print(f"\n--- 步骤 4: 可视化协同规划结果 ---")
        center_latlon = self.area_gdf_latlon.unary_union.centroid.coords[0][::-1]
        m = folium.Map(location=center_latlon, zoom_start=14, tiles="CartoDB positron")
        folium.GeoJson(
            self.area_gdf_latlon,
            style_function=lambda x: {'color': 'black', 'weight': 2.5, 'fillOpacity': 0.05, 'fillColor': 'black'},
            name='总任务区域', tooltip='总任务区域'
        ).add_to(m)
        if self.ground_station and self.ground_station_coverage_utm:
            gs_group = folium.FeatureGroup(name="地面站", show=True).add_to(m)
            gs_coverage_latlon = gpd.GeoSeries([self.ground_station_coverage_utm], crs=self.utm_crs).to_crs(self.original_crs)
            gs_point_latlon = gpd.GeoSeries([self.ground_station['geom_utm']], crs=self.utm_crs).to_crs(self.original_crs).iloc[0]
            folium.GeoJson(gs_coverage_latlon,
                           style_function=lambda x: {'color': 'red', 'weight': 2, 'fillColor': 'red', 'fillOpacity': 0.3},
                           tooltip=f"地面站观测范围 (半径: {self.ground_station['observation_radius_m']} m)"
                           ).add_to(gs_group)
            folium.Marker(
                location=[gs_point_latlon.y, gs_point_latlon.x],
                popup="地面观测站",
                icon=folium.Icon(color='red', icon='broadcast-tower', prefix='fa')
            ).add_to(gs_group)
        colors = plt.cm.get_cmap('viridis', self.num_uavs)
        for i, result in enumerate(self.results):
            uav_id = result['uav_id']
            color_hex = plt.cm.colors.to_hex(colors(i))
            feature_group = folium.FeatureGroup(name=f"无人机 {uav_id}", show=True).add_to(m)
            sub_area_utm = result.get('sub_area_utm')
            if sub_area_utm and not sub_area_utm.is_empty:
                sub_area_latlon = gpd.GeoSeries([sub_area_utm], crs=self.utm_crs).to_crs(self.original_crs)
                folium.GeoJson(sub_area_latlon,
                               style_function=lambda x, c=color_hex: {'color': c, 'weight': 1.5, 'fillColor': c, 'fillOpacity': 0.25},
                               tooltip=f'无人机 {uav_id} 分配区域').add_to(feature_group)
            path_utm = result.get('path_utm')
            if path_utm and not path_utm.is_empty:
                uav = result['uav_params']
                coverage_poly_utm = path_utm.buffer(uav['swath_width'] / 2, cap_style=2)
                path_latlon = gpd.GeoSeries([path_utm], crs=self.utm_crs).to_crs(self.original_crs)
                coverage_latlon = gpd.GeoSeries([coverage_poly_utm], crs=self.utm_crs).to_crs(self.original_crs)
                folium.GeoJson(coverage_latlon,
                               style_function=lambda x, c=color_hex: {'color': 'transparent', 'fillColor': c, 'fillOpacity': 0.4},
                               tooltip=f'无人机 {uav_id} 覆盖范围').add_to(feature_group)
                folium.GeoJson(path_latlon, style_function=lambda x, c=color_hex: {'color': c, 'weight': 2.5},
                               tooltip=f"无人机 {uav_id} 路径").add_to(feature_group)
        folium.LayerControl(collapsed=False).add_to(m)
        m.save(output_file)
        print(f"可视化地图已保存至: {output_file}")

    def get_results_as_json(self):
        summary_data = {
            "total_area_sqm": self.total_area_shape_utm.area,
            "final_collaborative_coverage_percentage": self.coverage_percentage,
            "ground_station_contribution": {},
            "uav_results": []
        }
        if self.ground_station and self.ground_station_coverage_utm:
            gs_coverage_in_area = self.total_area_shape_utm.intersection(self.ground_station_coverage_utm)
            summary_data["ground_station_contribution"] = {
                "coords_latlon": self.ground_station['coords_latlon'],
                "observation_radius_m": self.ground_station['observation_radius_m'],
                "covered_area_sqm": gs_coverage_in_area.area
            }
        for res in self.results:
            uav_p = res['uav_params']
            sub_area_utm = res.get('sub_area_utm')
            sub_area_latlon_geom = None
            if sub_area_utm and not sub_area_utm.is_empty:
                sub_area_latlon = gpd.GeoSeries([sub_area_utm], crs=self.utm_crs).to_crs(self.original_crs)
                sub_area_latlon_geom = sub_area_latlon.iloc[0].__geo_interface__
            uav_result = {
                "uav_id": res['uav_id'],
                "is_feasible": res.get('is_feasible', False),
                "assigned_area_sqm": sub_area_utm.area if sub_area_utm else 0,
                "path_length_m": res.get('path_length', 0),
                "estimated_flight_time_s": res.get('flight_duration_needed', 0),
                "max_flight_time_s": uav_p['flight_time'],
                "assigned_area_geojson": sub_area_latlon_geom
            }
            summary_data["uav_results"].append(uav_result)
        return summary_data

    def print_summary_report(self):
        print("\n\n" + "=" * 50)
        print(" " * 15 + "空地协同观测规划总结报告")
        print("=" * 50)
        if self.ground_station and self.ground_station_coverage_utm:
            gs_coverage_in_area = self.total_area_shape_utm.intersection(self.ground_station_coverage_utm)
            print("[地面站贡献]")
            print(f"  - 位置 (Lon, Lat): {self.ground_station['coords_latlon']}")
            print(f"  - 观测半径: {self.ground_station['observation_radius_m']} m")
            print(f"  - 有效覆盖面积: {gs_coverage_in_area.area:.2f} m²")
            print("-" * 50)
        print("[无人机机队任务详情]")
        for res in self.results:
            uav = res['uav_params']
            status = "✅ 可行" if res.get('is_feasible', False) else "❌ 超出续航"
            print(f"\n  [无人机 ID: {res['uav_id']}]")
            print(f"    - 分配区域面积: {res.get('sub_area_utm', Polygon()).area:.2f} m²")
            print(f"    - 规划路径长度: {res.get('path_length', 0):.2f} m")
            print(f"    - 预计飞行时间: {res.get('flight_duration_needed', 0):.2f} s / {uav['flight_time']} s")
            print(f"    - 任务可行性: {status}")
        print("\n" + "=" * 50)
        print(f"最终协同总覆盖率: {self.coverage_percentage:.2f}%")
        print("=" * 50)


# ==============================================================================
# 4. 主执行流程 (Main Execution Flow) - 无需修改
# ==============================================================================
if __name__ == '__main__':
    GEOJSON_FILE = "wuhan_east_lake.geojson"
    create_wuhan_geojson(GEOJSON_FILE)

    UAV_FLEET = [
        {'id': 1, 'speed': 25.0, 'flight_time': 3000, 'swath_width': 30},
        {'id': 2, 'speed': 25.0, 'flight_time': 3000, 'swath_width': 40},
        {'id': 3, 'speed': 20.0, 'flight_time': 2400, 'swath_width': 25},
        {'id': 4, 'speed': 20.0, 'flight_time': 2400, 'swath_width': 30},
    ]

    GROUND_STATION = {
        'coords_latlon': [114.405, 30.547],
        'observation_radius_m': 600
    }

    planner = CollaborativePlanner(
        geojson_path=GEOJSON_FILE,
        uavs_params=UAV_FLEET,
        ground_station_params=GROUND_STATION
    )

    if not planner.pre_check_feasibility():
        sys.exit("规划终止，请调整无人机参数或更换机队。")

    planner.decompose_area_and_assign()
    planner.plan_paths_for_all()
    planner.calculate_coverage()
    planner.visualize_plan()

    results_data = planner.get_results_as_json()
    json_output_file = "collaborative_planning_results.json"
    with open(json_output_file, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, ensure_ascii=False, indent=4)
    print(f"JSON格式的结果已保存至: {json_output_file}")

    planner.print_summary_report()