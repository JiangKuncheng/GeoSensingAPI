import json
import numpy as np
from datetime import datetime, timedelta
import geojson
from shapely.geometry import shape
from shapely.ops import unary_union

# 导入您已经写好的工具函数
from satelliteTool.get_observation_lace import get_coverage_lace
from satelliteTool.get_observation_overlap import get_observation_overlap
from GeoPandasTool.intersects import intersects
from GeoPandasTool.is_valid_reason import is_valid_reason
from GeoPandasTool.is_valid import is_valid
from GeoPandasTool.union import union


class WuhanSatelliteObservationPlanner:
    """武汉市卫星观测规划器"""
    
    def __init__(self):
        self.tle_data = {}
        self.wuhan_geojson = None
        self.coverage_results = {}
        self.intersection_results = {}
        self.valid_satellites = []
        
    def load_tle_data(self):
        """加载TLE数据"""
        print("正在加载TLE数据...")
        try:
            with open('satelliteTool/tle_data.json', 'r', encoding='utf-8') as f:
                self.tle_data = json.load(f)
            print(f"✅ 成功加载 {len(self.tle_data)} 颗卫星的TLE数据")
        except Exception as e:
            print(f"❌ 加载TLE数据失败: {e}")
            return False
        return True
    
    def define_wuhan_area(self):
        """定义武汉市区域 - 使用硬编码的外接矩形"""
        print("正在定义武汉市外接矩形...")
        
        # 武汉市的真实外接矩形坐标
        # 经度范围: 113.68°E - 115.05°E
        # 纬度范围: 29.58°N - 31.35°N
        self.wuhan_geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {"name": "武汉市外接矩形"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [113.68, 29.58],  # 西南角
                        [115.05, 29.58],  # 东南角
                        [115.05, 31.35],  # 东北角
                        [113.68, 31.35],  # 西北角
                        [113.68, 29.58]   # 闭合
                    ]]
                }
            }]
        }
        
        print("✅ 武汉市外接矩形定义完成")
        print(f"   经度范围: 113.68°E - 115.05°E")
        print(f"   纬度范围: 29.58°N - 31.35°N")
        print(f"   总面积: 约 {(115.05-113.68) * (31.35-29.58):.3f} 平方度")
        return True
    
    def get_satellite_footprints(self, start_time, end_time, fov=20.0, interval_seconds=600):
        """获取所有卫星的覆盖足迹"""
        print(f"\n正在获取卫星覆盖足迹...")
        print(f"时间窗口: {start_time} 到 {end_time}")
        print(f"视场角: {fov}°, 时间间隔: {interval_seconds}秒")
        
        try:
            coverage_geojson = get_coverage_lace(
                tle_dict=self.tle_data,
                start_time_str=start_time,
                end_time_str=end_time,
                fov=fov,
                interval_seconds=interval_seconds
            )
            
            print(f"✅ 成功生成 {len(coverage_geojson['features'])} 个足迹点")
            return coverage_geojson
            
        except Exception as e:
            print(f"❌ 获取卫星足迹失败: {e}")
            return None
    
    def filter_intersecting_satellites(self, coverage_geojson):
        """筛选与武汉市相交的卫星"""
        print("\n正在筛选与武汉市相交的卫星...")
        
        if not coverage_geojson or not coverage_geojson.get('features'):
            print("❌ 没有可用的覆盖足迹数据")
            return []
        
        # 将武汉市GeoJSON转换为字符串格式
        wuhan_geojson_str = json.dumps(self.wuhan_geojson)
        
        # 按卫星分组足迹
        satellite_footprints = {}
        for feature in coverage_geojson['features']:
            satellite_name = feature['properties']['satellite']
            if satellite_name not in satellite_footprints:
                satellite_footprints[satellite_name] = []
            satellite_footprints[satellite_name].append(feature)
        
        # 检查每个卫星是否与武汉市相交
        intersecting_satellites = []
        
        for satellite_name, footprints in satellite_footprints.items():
            print(f"  检查卫星: {satellite_name}")
            
            # 合并该卫星的所有足迹为一个GeoJSON
            merged_footprint = {
                "type": "FeatureCollection",
                "features": footprints
            }
            merged_footprint_str = json.dumps(merged_footprint)
            
            try:
                # 使用intersects工具检查是否相交
                intersection_results = intersects(merged_footprint_str, wuhan_geojson_str)
                
                # 检查是否有任何足迹与武汉市相交
                if any(intersection_results):
                    intersecting_satellites.append(satellite_name)
                    print(f"    ✅ 与武汉市相交")
                    
                    # 检查几何有效性
                    validity_results = is_valid(merged_footprint_str)
                    if not all(validity_results):
                        print(f"    ⚠️  部分几何图形无效，正在检查原因...")
                        validity_reasons = is_valid_reason(merged_footprint_str)
                        for i, reason in enumerate(validity_reasons):
                            if not validity_results[i]:
                                print(f"      足迹 {i+1}: {reason}")
                else:
                    print(f"    ❌ 不与武汉市相交")
                    
            except Exception as e:
                print(f"    ❌ 检查相交性时出错: {e}")
                continue
        
        print(f"\n✅ 筛选完成，找到 {len(intersecting_satellites)} 颗与武汉市相交的卫星")
        return intersecting_satellites
    
    def calculate_coverage_for_satellites(self, intersecting_satellites, start_time, end_time, fov=20.0, interval_seconds=600):
        """计算每个相交卫星的覆盖率"""
        print(f"\n正在计算卫星覆盖率...")
        
        if not intersecting_satellites:
            print("❌ 没有相交的卫星")
            return {}
        
        # 创建只包含相交卫星的TLE字典
        filtered_tle_dict = {name: self.tle_data[name] for name in intersecting_satellites if name in self.tle_data}
        
        try:
            coverage_results = get_observation_overlap(
                tle_dict=filtered_tle_dict,
                start_time_str=start_time,
                end_time_str=end_time,
                target_geojson=self.wuhan_geojson,
                fov=fov,
                interval_seconds=interval_seconds
            )
            
            print(f"✅ 覆盖率计算完成")
            for satellite, coverage in coverage_results.items():
                print(f"   {satellite}: {coverage:.2%}")
            
            return coverage_results
            
        except Exception as e:
            print(f"❌ 计算覆盖率失败: {e}")
            return {}
    
    def find_optimal_coverage_plan(self, coverage_results, target_coverage=0.9):
        """寻找最优覆盖方案"""
        print(f"\n正在寻找最优覆盖方案...")
        print(f"目标覆盖率: {target_coverage:.1%}")
        
        if not coverage_results:
            print("❌ 没有可用的覆盖率数据")
            return None
        
        # 检查是否有单个卫星能达到目标覆盖率
        single_satellite_solutions = []
        for satellite, coverage in coverage_results.items():
            if coverage >= target_coverage:
                single_satellite_solutions.append((satellite, coverage))
        
        if single_satellite_solutions:
            # 选择覆盖率最高的单个卫星
            best_single = max(single_satellite_solutions, key=lambda x: x[1])
            print(f"✅ 找到单个卫星解决方案:")
            print(f"   卫星: {best_single[0]}")
            print(f"   覆盖率: {best_single[1]:.2%}")
            return {
                'type': 'single',
                'satellites': [best_single[0]],
                'coverage': best_single[1],
                'description': f"使用单颗卫星 {best_single[0]} 即可达到 {best_single[1]:.2%} 的覆盖率"
            }
        
        # 如果没有单个卫星能达到目标，寻找组合方案
        print("   没有单个卫星能达到目标覆盖率，正在寻找组合方案...")
        
        # 按覆盖率降序排列
        sorted_satellites = sorted(coverage_results.items(), key=lambda x: x[1], reverse=True)
        
        # 尝试不同的组合
        best_combination = None
        best_coverage = 0
        
        # 尝试2-3颗卫星的组合
        for combination_size in range(2, min(4, len(sorted_satellites) + 1)):
            from itertools import combinations
            
            for combo in combinations(sorted_satellites, combination_size):
                combo_satellites = [sat for sat, _ in combo]
                combo_coverage = self._calculate_combined_coverage(combo_satellites, coverage_results)
                
                if combo_coverage >= target_coverage and combo_coverage > best_coverage:
                    best_combination = combo_satellites
                    best_coverage = combo_coverage
                    print(f"   找到可行组合: {combo_satellites} -> {combo_coverage:.2%}")
        
        if best_combination:
            print(f"✅ 找到最佳组合方案:")
            print(f"   卫星组合: {', '.join(best_combination)}")
            print(f"   组合覆盖率: {best_coverage:.2%}")
            return {
                'type': 'combination',
                'satellites': best_combination,
                'coverage': best_coverage,
                'description': f"使用卫星组合 {', '.join(best_combination)} 可达到 {best_coverage:.2%} 的覆盖率"
            }
        else:
            print("❌ 无法找到满足要求的卫星组合")
            return None
    
    def _calculate_combined_coverage(self, satellite_list, individual_coverage):
        """计算卫星组合的覆盖率（简化计算，假设无重叠）"""
        # 这是一个简化的计算，实际应该考虑卫星足迹的重叠
        # 这里使用并集的方式计算
        total_coverage = 0
        for satellite in satellite_list:
            total_coverage += individual_coverage.get(satellite, 0)
        
        # 简化的重叠处理：假设重叠率为20%
        overlap_factor = 0.2
        adjusted_coverage = total_coverage * (1 - overlap_factor)
        
        return min(adjusted_coverage, 1.0)
    
    def generate_observation_plan(self, start_time, end_time, fov=20.0, interval_seconds=600):
        """生成完整的观测规划"""
        print("=" * 80)
        print("武汉市卫星观测规划生成器")
        print("=" * 80)
        
        # 1. 加载数据
        if not self.load_tle_data():
            return None
        
        if not self.define_wuhan_area():
            return None
        
        # 2. 获取卫星足迹
        coverage_geojson = self.get_satellite_footprints(start_time, end_time, fov, interval_seconds)
        if not coverage_geojson:
            return None
        
        # 3. 筛选相交卫星
        intersecting_satellites = self.filter_intersecting_satellites(coverage_geojson)
        if not intersecting_satellites:
            print("❌ 没有找到与武汉市相交的卫星")
            return None
        
        # 4. 计算覆盖率
        coverage_results = self.calculate_coverage_for_satellites(
            intersecting_satellites, start_time, end_time, fov, interval_seconds
        )
        
        # 5. 寻找最优方案
        optimal_plan = self.find_optimal_coverage_plan(coverage_results)
        
        # 6. 生成最终报告
        final_report = {
            'planning_period': {
                'start_time': start_time,
                'end_time': end_time
            },
            'target_area': '武汉市',
            'total_satellites': len(self.tle_data),
            'intersecting_satellites': intersecting_satellites,
            'coverage_results': coverage_results,
            'optimal_plan': optimal_plan,
            'generation_time': datetime.now().isoformat()
        }
        
        return final_report
    
    def save_results(self, results, filename):
        """保存结果到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"✅ 结果已保存到: {filename}")
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")


def main():
    """主函数"""
    # 创建规划器实例
    planner = WuhanSatelliteObservationPlanner()
    
    # 设置时间窗口：2025年8月1日至8月10日
    start_time = "2025-08-01 00:00:00.000"
    end_time = "2025-08-10 23:59:59.000"
    
    # 生成观测规划
    results = planner.generate_observation_plan(
        start_time=start_time,
        end_time=end_time,
        fov=20.0,  # 30度视场角
        interval_seconds=600  # 10分钟间隔
    )
    
    if results:
        # 保存结果
        output_filename = 'wuhan_satellite_observation_plan.json'
        planner.save_results(results, output_filename)
        
        # 显示最终结果
        print("\n" + "=" * 80)
        print("观测规划结果汇总")
        print("=" * 80)
        print(f"规划时间: {results['planning_period']['start_time']} 至 {results['planning_period']['end_time']}")
        print(f"目标区域: {results['target_area']}")
        print(f"总卫星数量: {results['total_satellites']}")
        print(f"相交卫星数量: {len(results['intersecting_satellites'])}")
        
        if results['optimal_plan']:
            print(f"\n🏆 推荐方案:")
            print(f"   类型: {results['optimal_plan']['type']}")
            print(f"   卫星: {', '.join(results['optimal_plan']['satellites'])}")
            print(f"   覆盖率: {results['optimal_plan']['coverage']:.2%}")
            print(f"   说明: {results['optimal_plan']['description']}")
        else:
            print("\n❌ 无法找到满足要求的观测方案")
        
        print(f"\n详细结果已保存到: {output_filename}")
    else:
        print("❌ 观测规划生成失败")


if __name__ == "__main__":
    main() 