import requests
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class ComprehensiveAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {}
        self.geojson_files = {
            "湖北省": "geojson/Hubei.geojson",
            "武汉市": "geojson/Wuhan.geojson", 
            "上海市": "geojson/Shanghai.geojson",
            "纽约市": "geojson/New_York.geojson"
        }
        
        # 创建输出文件夹
        self.output_dir = "api_test_output"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # 为每个API创建子文件夹
        self.api_output_dirs = {}
        
    def get_api_output_dir(self, api_name: str) -> str:
        """获取API的输出目录"""
        if api_name not in self.api_output_dirs:
            # 清理API名称，移除特殊字符
            clean_name = api_name.replace(" ", "_").replace("-", "_").replace("/", "_")
            api_dir = os.path.join(self.output_dir, clean_name)
            if not os.path.exists(api_dir):
                os.makedirs(api_dir)
            self.api_output_dirs[api_name] = api_dir
        return self.api_output_dirs[api_name]
    
    def save_geojson_result(self, api_name: str, place_name: str, result: Any) -> Optional[str]:
        """保存GeoJSON结果到文件"""
        try:
            output_dir = self.get_api_output_dir(api_name)
            
            # 清理地名，用作文件名
            clean_place_name = place_name.replace(" ", "_").replace("-", "_").replace("/", "_")
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{clean_place_name}_{timestamp}.geojson"
            filepath = os.path.join(output_dir, filename)
            
            # 保存GeoJSON数据
            if isinstance(result, dict):
                # 如果结果是字典格式的GeoJSON
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            elif isinstance(result, str):
                # 如果结果是字符串格式的GeoJSON
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(result)
            else:
                # 其他格式，转换为JSON保存
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            
            return filepath
        except Exception as e:
            print(f"保存GeoJSON文件失败: {e}")
            return None
    
    def save_api_results(self, api_name: str, response: Dict) -> Dict[str, str]:
        """保存API返回的所有GeoJSON结果"""
        saved_files = {}
        
        if not response:
            return saved_files
            
        for place_name, result in response.items():
            if result is not None:
                # 检查结果是否包含GeoJSON数据
                if isinstance(result, dict) and result.get("type") in ["Feature", "FeatureCollection"]:
                    filepath = self.save_geojson_result(api_name, place_name, result)
                    if filepath:
                        saved_files[place_name] = filepath
                elif isinstance(result, str) and ("Feature" in result or "geometry" in result):
                    # 尝试解析为JSON
                    try:
                        json_data = json.loads(result)
                        if isinstance(json_data, dict) and json_data.get("type") in ["Feature", "FeatureCollection"]:
                            filepath = self.save_geojson_result(api_name, place_name, json_data)
                            if filepath:
                                saved_files[place_name] = filepath
                    except:
                        # 如果不是JSON，直接保存字符串
                        filepath = self.save_geojson_result(api_name, place_name, result)
                        if filepath:
                            saved_files[place_name] = filepath
                elif isinstance(result, list):
                    # 处理列表结果
                    for i, item in enumerate(result):
                        if isinstance(item, dict) and item.get("type") in ["Feature", "FeatureCollection"]:
                            filepath = self.save_geojson_result(api_name, f"{place_name}_{i}", item)
                            if filepath:
                                saved_files[f"{place_name}_{i}"] = filepath
                elif isinstance(result, bool) or isinstance(result, (int, float)):
                    # 对于布尔值或数值结果，保存为JSON格式
                    result_data = {"result": result, "place": place_name, "api": api_name}
                    filepath = self.save_geojson_result(api_name, f"{place_name}_result", result_data)
                    if filepath:
                        saved_files[place_name] = filepath
        
        return saved_files
        
    def log_test_result(self, api_name: str, success: bool, response: Optional[Dict] = None, error: Optional[str] = None):
        """记录测试结果"""
        saved_files = {}
        if success and response:
            saved_files = self.save_api_results(api_name, response)
            
        self.test_results[api_name] = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "response": response,
            "error": error,
            "saved_files": saved_files,
            "analysis": self.analyze_result(response, error)
        }
        
    def print_test_result(self, api_name: str, success: bool, response: Optional[Dict] = None, error: Optional[str] = None):
        """打印测试结果"""
        print(f"\n{'='*60}")
        print(f"测试API: {api_name}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"状态: {'✓ 成功' if success else '✗ 失败'}")
        
        if success and response:
            print(f"返回结果: {json.dumps(response, ensure_ascii=False, indent=2)}")
            
            # 显示保存的文件
            saved_files = self.save_api_results(api_name, response)
            if saved_files:
                print(f"📁 保存的GeoJSON文件:")
                for place_name, filepath in saved_files.items():
                    print(f"   {place_name}: {filepath}")
            
            # 分析返回结果
            analysis = self.analyze_result(response, None)
            if analysis:
                print(f"结果分析: {analysis}")
        elif error:
            print(f"错误信息: {error}")
            analysis = self.analyze_result(None, error)
            if analysis:
                print(f"错误分析: {analysis}")
        print(f"{'='*60}")
    
    def analyze_result(self, response: Optional[Dict], error: Optional[str]) -> Optional[str]:
        """分析API返回结果或错误"""
        if error:
            if "Connection refused" in error or "Failed to establish" in error:
                return "API服务器未启动或端口错误"
            elif "timeout" in error.lower():
                return "请求超时，可能是API处理时间过长"
            elif "404" in error:
                return "API端点不存在"
            elif "500" in error:
                return "服务器内部错误"
            else:
                return f"网络或服务器错误: {error}"
        
        if response is None:
            return "API返回null结果"
        
        # 检查返回结果是否为空或null
        if not response:
            return "API返回空结果"
        
        # 检查特定字段
        if isinstance(response, dict):
            if all(v is None for v in response.values()):
                return "所有返回字段都为null"
            elif any(v is None for v in response.values()):
                null_fields = [k for k, v in response.items() if v is None]
                return f"部分字段为null: {null_fields}"
        
        return None
    
    def test_api(self, endpoint: str, payload: Dict, api_name: str) -> bool:
        """通用API测试方法"""
        try:
            url = f"{self.base_url}/{endpoint}"
            print(f"正在测试 {api_name}...")
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            self.log_test_result(api_name, True, result)
            self.print_test_result(api_name, True, result)
            return True
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"连接错误: {str(e)}"
            self.log_test_result(api_name, False, error=error_msg)
            self.print_test_result(api_name, False, error=error_msg)
            return False
        except requests.exceptions.Timeout as e:
            error_msg = f"请求超时: {str(e)}"
            self.log_test_result(api_name, False, error=error_msg)
            self.print_test_result(api_name, False, error=error_msg)
            return False
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP错误 {response.status_code}: {str(e)}"
            self.log_test_result(api_name, False, error=error_msg)
            self.print_test_result(api_name, False, error=error_msg)
            return False
        except Exception as e:
            error_msg = str(e)
            self.log_test_result(api_name, False, error=error_msg)
            self.print_test_result(api_name, False, error=error_msg)
            return False
    
    def test_satellite_apis(self):
        """测试卫星相关API"""
        print("\n" + "🚀" * 20 + " 卫星相关API测试 " + "🚀" * 20)
        
        # 1. 获取TLE数据
        tle_payload = {
            "satellite_names": ["ISS (ZARYA)", "NOAA 19", "TERRA", "AQUA"]
        }
        self.test_api("get_tle", tle_payload, "获取TLE数据")
        
        # 2. 获取边界数据
        boundary_payload = {
            "place_names": ["Wuhan", "Shanghai", "New York"]
        }
        self.test_api("get_boundary", boundary_payload, "获取行政边界")
        
        # 3. 计算轨道速度
        velocity_payload = {
            "tle_dict": {
                "ISS (ZARYA)": "1 25544U 98067A   24001.50000000  .00000000  00000+0  00000+0 0    06\n2 25544  51.6400 100.0000 0000001   0.0000   0.0000 15.50000000    01",
                "NOAA 19": "1 33591U 09005A   24001.50000000  .00000000  00000+0  00000+0 0    08\n2 33591  99.2000 100.0000 0000001   0.0000   0.0000 14.20000000    01"
            }
        }
        self.test_api("calculate_velocity", velocity_payload, "计算轨道速度")
        
        # 4. 计算轨道半径
        radius_payload = {
            "tle_dict": {
                "ISS (ZARYA)": "1 25544U 98067A   24001.50000000  .00000000  00000+0  00000+0 0    06\n2 25544  51.6400 100.0000 0000001   0.0000   0.0000 15.50000000    01"
            }
        }
        self.test_api("calculate_orbit_radius", radius_payload, "计算轨道半径")
    
    def test_geometric_apis(self):
        """测试几何运算API"""
        print("\n" + "📐" * 20 + " 几何运算API测试 " + "📐" * 20)
        
        # 1. 计算面积
        area_payload = {
            "place_geojson_dict": self.geojson_files
        }
        self.test_api("area", area_payload, "计算面积")
        
        # 2. 计算边界
        boundary_payload = {
            "place_geojson_dict": self.geojson_files,
            "multiInvocation": False
        }
        self.test_api("boundary", boundary_payload, "计算边界")
        
        # 3. 计算边界框
        bounds_payload = {
            "place_geojson_dict": self.geojson_files,
            "multiInvocation": False
        }
        self.test_api("bounds", bounds_payload, "计算边界框")
        
        # 4. 计算缓冲区
        buffer_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]},
            "distance": 0.01
        }
        self.test_api("buffer", buffer_payload, "计算缓冲区")
        
        # 5. 计算质心
        centroid_payload = {
            "place_geojson_dict": self.geojson_files
        }
        self.test_api("centroid", centroid_payload, "计算质心")
        
        # 6. 矩形裁剪
        clip_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]},
            "xmin": 114.0, "ymin": 30.0, "xmax": 115.0, "ymax": 31.0
        }
        self.test_api("clip_by_rect", clip_payload, "矩形裁剪")
        
        # 7. 凹壳计算
        concave_hull_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]},
            "alpha": 0.1
        }
        self.test_api("concave_hull", concave_hull_payload, "凹壳计算")
        
        # 8. 凸壳计算
        convex_hull_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]}
        }
        self.test_api("convex-hull", convex_hull_payload, "凸壳计算")
        
        # 9. 包络线
        envelope_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]}
        }
        self.test_api("envelope", envelope_payload, "计算包络线")
        
        # 10. 外边界
        exterior_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]}
        }
        self.test_api("exterior", exterior_payload, "计算外边界")
        
        # 11. 长度计算
        length_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]}
        }
        self.test_api("length", length_payload, "计算长度")
        
        # 12. 最小包围半径
        mbr_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]}
        }
        self.test_api("minimum_bounding_radius", mbr_payload, "最小包围半径")
        
        # 13. 偏移曲线
        offset_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]},
            "distance": 0.01,
            "side": "right"
        }
        self.test_api("offset_curve", offset_payload, "偏移曲线")
        
        # 14. 简化几何
        simplify_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]},
            "tolerance": 0.001
        }
        self.test_api("simplify", simplify_payload, "简化几何")
        
        # 15. 总边界框
        total_bounds_payload = {
            "place_geojson_dict": self.geojson_files
        }
        self.test_api("total_bounds", total_bounds_payload, "总边界框")
    
    def test_spatial_relationship_apis(self):
        """测试空间关系API"""
        print("\n" + "🔗" * 20 + " 空间关系API测试 " + "🔗" * 20)
        
        # 准备测试数据对
        test_pairs = [
            {
                "place1": "武汉市",
                "geojson1": self.geojson_files["武汉市"],
                "place2": "湖北省", 
                "geojson2": self.geojson_files["湖北省"]
            },
            {
                "place1": "上海市",
                "geojson1": self.geojson_files["上海市"],
                "place2": "武汉市",
                "geojson2": self.geojson_files["武汉市"]
            }
        ]
        
        # 1. 包含关系
        contains_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ]
        }
        self.test_api("contains", contains_payload, "包含关系检查")
        
        # 2. 严格包含关系
        contains_properly_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ]
        }
        self.test_api("contains-properly", contains_properly_payload, "严格包含关系检查")
        
        # 3. 被包含关系
        covered_by_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ]
        }
        self.test_api("covered-by", covered_by_payload, "被包含关系检查")
        
        # 4. 覆盖关系
        covers_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ]
        }
        self.test_api("covers", covers_payload, "覆盖关系检查")
        
        # 5. 相交关系
        intersects_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ]
        }
        self.test_api("intersects", intersects_payload, "相交关系检查")
        
        # 6. 交叉关系
        crosses_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ]
        }
        self.test_api("crosses", crosses_payload, "交叉关系检查")
        
        # 7. 分离关系
        disjoint_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ]
        }
        self.test_api("disjoint", disjoint_payload, "分离关系检查")
        
        # 8. 重叠关系
        overlaps_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ]
        }
        self.test_api("overlaps", overlaps_payload, "重叠关系检查")
        
        # 9. 接触关系
        touches_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ]
        }
        self.test_api("touches", touches_payload, "接触关系检查")
        
        # 10. 内部关系
        within_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ]
        }
        self.test_api("within", within_payload, "内部关系检查")
        
        # 11. 距离计算
        distance_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ]
        }
        self.test_api("distance", distance_payload, "距离计算")
        
        # 12. 距离范围内
        dwithin_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ],
            "distance": 1.0
        }
        self.test_api("dwithin", dwithin_payload, "距离范围内检查")
        
        # 13. 几何相等
        geom_equals_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ]
        }
        self.test_api("geom_equals", geom_equals_payload, "几何相等检查")
        
        # 14. 近似相等
        geom_almost_equal_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ],
            "tolerance": 1e-6
        }
        self.test_api("geom_almost_equal", geom_almost_equal_payload, "近似相等检查")
        
        # 15. 精确相等
        geom_equals_exact_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ],
            "tolerance": 1e-9
        }
        self.test_api("geom_equals_exact", geom_equals_exact_payload, "精确相等检查")
    
    def test_geometric_operation_apis(self):
        """测试几何运算API"""
        print("\n" + "⚙️" * 20 + " 几何运算API测试 " + "⚙️" * 20)
        
        # 准备测试数据对
        test_pairs = [
            {
                "place1": "武汉市",
                "geojson1": self.geojson_files["武汉市"],
                "place2": "湖北省", 
                "geojson2": self.geojson_files["湖北省"]
            }
        ]
        
        # 1. 交集运算
        intersection_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ]
        }
        self.test_api("intersection", intersection_payload, "交集运算")
        
        # 2. 差集运算
        difference_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ]
        }
        self.test_api("difference", difference_payload, "差集运算")
        
        # 3. 并集运算
        union_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ]
        }
        self.test_api("union", union_payload, "并集运算")
        
        # 4. 对称差集运算
        symmetric_difference_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ]
        }
        self.test_api("symmetric_difference", symmetric_difference_payload, "对称差集运算")
        
        # 5. 最短线
        shortest_line_payload = {
            "input_list": [
                {
                    "place1": pair["place1"], "geojson1": pair["geojson1"],
                    "place2": pair["place2"], "geojson2": pair["geojson2"]
                }
                for pair in test_pairs
            ]
        }
        self.test_api("shortest_line_between_two", shortest_line_payload, "最短线计算")
    
    def test_geometric_property_apis(self):
        """测试几何属性API"""
        print("\n" + "🔍" * 20 + " 几何属性API测试 " + "🔍" * 20)
        
        # 1. 逆时针检查
        is_ccw_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]}
        }
        self.test_api("is_ccw", is_ccw_payload, "逆时针检查")
        
        # 2. 闭合检查
        is_closed_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]}
        }
        self.test_api("is_closed", is_closed_payload, "闭合检查")
        
        # 3. 空几何检查
        is_empty_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]}
        }
        self.test_api("is_empty", is_empty_payload, "空几何检查")
        
        # 4. 环检查
        is_ring_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]}
        }
        self.test_api("is_ring", is_ring_payload, "环检查")
        
        # 5. 简单几何检查
        is_simple_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]}
        }
        self.test_api("is_simple", is_simple_payload, "简单几何检查")
        
        # 6. 有效性检查
        is_valid_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]}
        }
        self.test_api("is_valid", is_valid_payload, "有效性检查")
        
        # 7. 有效性原因
        is_valid_reason_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]}
        }
        self.test_api("is_valid_reason", is_valid_reason_payload, "有效性原因")
    
    def test_geometric_transformation_apis(self):
        """测试几何变换API"""
        print("\n" + "🔄" * 20 + " 几何变换API测试 " + "🔄" * 20)
        
        # 1. 旋转
        rotate_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]},
            "angle": 45.0,
            "origin": "centroid"
        }
        self.test_api("rotate", rotate_payload, "几何旋转")
        
        # 2. 缩放
        scale_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]},
            "xfact": 1.1,
            "yfact": 1.1,
            "origin": "center"
        }
        self.test_api("scale", scale_payload, "几何缩放")
        
        # 3. 平移
        translate_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]},
            "xoff": 0.01,
            "yoff": 0.01
        }
        self.test_api("translate", translate_payload, "几何平移")
        
        # 4. 反转
        reverse_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]}
        }
        self.test_api("reverse", reverse_payload, "几何反转")
        
        # 5. 线合并
        line_merge_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]}
        }
        self.test_api("line_merge", line_merge_payload, "线合并")
        
        # 6. 移除重复点
        remove_points_payload = {
            "place_geojson_dict": {"武汉市": self.geojson_files["武汉市"]}
        }
        self.test_api("remove_repeated_points", remove_points_payload, "移除重复点")
    
    def save_test_report(self):
        """保存测试报告"""
        report = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "successful_tests": sum(1 for result in self.test_results.values() if result["success"]),
                "failed_tests": sum(1 for result in self.test_results.values() if not result["success"]),
                "test_time": datetime.now().isoformat(),
                "output_directory": self.output_dir
            },
            "test_results": self.test_results
        }
        
        # 保存详细报告
        with open("api_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 保存摘要报告
        summary = []
        for api_name, result in self.test_results.items():
            summary.append({
                "api": api_name,
                "status": "成功" if result["success"] else "失败",
                "error": result.get("error", ""),
                "analysis": result.get("analysis", ""),
                "saved_files": result.get("saved_files", {})
            })
        
        with open("api_test_summary.txt", "w", encoding="utf-8") as f:
            f.write("API测试摘要报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总测试数: {len(self.test_results)}\n")
            f.write(f"成功数: {sum(1 for result in self.test_results.values() if result['success'])}\n")
            f.write(f"失败数: {sum(1 for result in self.test_results.values() if not result['success'])}\n")
            f.write(f"输出目录: {self.output_dir}\n")
            f.write("\n详细结果:\n")
            f.write("-" * 50 + "\n")
            
            for item in summary:
                f.write(f"{item['api']}: {item['status']}\n")
                if item['error']:
                    f.write(f"  错误: {item['error']}\n")
                if item['analysis']:
                    f.write(f"  分析: {item['analysis']}\n")
                if item['saved_files']:
                    f.write(f"  保存的文件:\n")
                    for place_name, filepath in item['saved_files'].items():
                        f.write(f"    {place_name}: {filepath}\n")
                f.write("\n")
        
        print(f"\n📊 测试报告已保存:")
        print(f"   详细报告: api_test_report.json")
        print(f"   摘要报告: api_test_summary.txt")
        print(f"   GeoJSON文件输出目录: {self.output_dir}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始全面API测试...")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"API服务器: {self.base_url}")
        print(f"测试数据: {list(self.geojson_files.keys())}")
        
        start_time = time.time()
        
        # 运行各类测试
        self.test_satellite_apis()
        self.test_geometric_apis()
        self.test_spatial_relationship_apis()
        self.test_geometric_operation_apis()
        self.test_geometric_property_apis()
        self.test_geometric_transformation_apis()
        
        end_time = time.time()
        
        # 生成测试报告
        self.save_test_report()
        
        # 打印最终统计
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"\n🎯 测试完成!")
        print(f"总测试数: {total_tests}")
        print(f"成功数: {successful_tests}")
        print(f"失败数: {failed_tests}")
        print(f"成功率: {successful_tests/total_tests*100:.1f}%")
        print(f"测试耗时: {end_time - start_time:.2f}秒")
        
        # 分析null结果
        self.analyze_null_results()
    
    def analyze_null_results(self):
        """分析null结果的原因"""
        print(f"\n🔍 NULL结果分析:")
        print("=" * 50)
        
        null_results = []
        for api_name, result in self.test_results.items():
            if result["success"] and result.get("analysis") and "null" in result["analysis"].lower():
                null_results.append((api_name, result["analysis"]))
        
        if null_results:
            print(f"发现 {len(null_results)} 个返回null结果的API:")
            for api_name, analysis in null_results:
                print(f"  - {api_name}: {analysis}")
            
            print(f"\n可能的原因:")
            print("  1. 输入数据格式不正确")
            print("  2. 几何对象类型不支持")
            print("  3. 计算过程中出现异常")
            print("  4. API实现逻辑问题")
        else:
            print("没有发现返回null结果的API")

if __name__ == "__main__":
    # 创建测试器实例
    tester = ComprehensiveAPITester()
    
    # 运行所有测试
    tester.run_all_tests() 