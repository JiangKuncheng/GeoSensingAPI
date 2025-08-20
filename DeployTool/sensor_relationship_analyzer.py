"""
传感器时空关系分析器

该模块提供传感器间时间和空间关系评估功能，包括：
1. 时间维度：竞争关系、互补关系
2. 空间维度：竞争关系、互补关系、增强关系

作者：GeoSensingAPI
"""

import math
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Union, Optional
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

class TimeRelationType(Enum):
    """时间关系类型"""
    COMPETITIVE = "时间竞争"
    COMPLEMENTARY = "时间互补"
    INDEPENDENT = "时间独立"

class SpaceRelationType(Enum):
    """空间关系类型"""
    COMPETITIVE = "空间竞争"
    COMPLEMENTARY = "空间互补"
    ENHANCED = "空间增强"
    INDEPENDENT = "空间独立"

@dataclass
class SensorParameters:
    """传感器参数类"""
    id: str
    # 空间参数
    latitude: float
    longitude: float
    coverage_radius: float  # 覆盖半径（km）
    
    # 时间参数
    start_time: datetime
    end_time: datetime
    
    # 观测参数
    observation_parameters: List[str]  # 如 ['temperature', 'humidity', 'pressure']
    observation_mechanism: str  # 如 'remote_sensing', 'in_situ', 'satellite'
    
    # 质量参数
    accuracy: float = 1.0  # 观测精度权重
    resolution: float = 1.0  # 时空分辨率权重
    reliability: float = 1.0  # 可靠性权重

class SensorRelationshipAnalyzer:
    """传感器关系分析器"""
    
    def __init__(self, time_tolerance: float = 0.1, space_tolerance: float = 0.1):
        """
        初始化分析器
        
        参数:
            time_tolerance: 时间重叠容忍度 (0-1)
            space_tolerance: 空间重叠容忍度 (0-1)
        """
        self.time_tolerance = time_tolerance
        self.space_tolerance = space_tolerance
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        计算两点间的球面距离（Haversine公式）
        
        返回:
            距离（公里）
        """
        R = 6371  # 地球半径（公里）
        
        # 转换为弧度
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine公式
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def calculate_time_overlap(self, sensor1: SensorParameters, sensor2: SensorParameters) -> float:
        """
        计算两个传感器的时间重叠比例
        
        返回:
            重叠比例 (0-1)
        """
        # 获取重叠时间段
        overlap_start = max(sensor1.start_time, sensor2.start_time)
        overlap_end = min(sensor1.end_time, sensor2.end_time)
        
        if overlap_start >= overlap_end:
            return 0.0  # 无重叠
        
        # 计算重叠时间长度
        overlap_duration = (overlap_end - overlap_start).total_seconds()
        
        # 计算各自的总时间长度
        sensor1_duration = (sensor1.end_time - sensor1.start_time).total_seconds()
        sensor2_duration = (sensor2.end_time - sensor2.start_time).total_seconds()
        
        # 计算相对于较短时间段的重叠比例
        min_duration = min(sensor1_duration, sensor2_duration)
        
        if min_duration == 0:
            return 0.0
        
        return overlap_duration / min_duration
    
    def calculate_space_overlap(self, sensor1: SensorParameters, sensor2: SensorParameters) -> float:
        """
        计算两个传感器的空间重叠比例
        
        返回:
            重叠比例 (0-1)
        """
        # 计算中心点距离
        distance = self.calculate_distance(
            sensor1.latitude, sensor1.longitude,
            sensor2.latitude, sensor2.longitude
        )
        
        # 计算覆盖半径
        r1 = sensor1.coverage_radius
        r2 = sensor2.coverage_radius
        
        # 如果距离大于两个半径之和，则无重叠
        if distance >= r1 + r2:
            return 0.0
        
        # 如果一个圆完全包含另一个圆
        if distance <= abs(r1 - r2):
            smaller_area = math.pi * min(r1, r2) ** 2
            larger_area = math.pi * max(r1, r2) ** 2
            return smaller_area / larger_area
        
        # 计算两个圆的交集面积
        # 使用几何公式计算圆-圆交集
        # A = r1²*arccos((d²+r1²-r2²)/(2*d*r1)) + r2²*arccos((d²+r2²-r1²)/(2*d*r2)) - 0.5*sqrt((-d+r1+r2)*(d+r1-r2)*(d-r1+r2)*(d+r1+r2))
        
        try:
            term1 = r1**2 * math.acos((distance**2 + r1**2 - r2**2) / (2 * distance * r1))
            term2 = r2**2 * math.acos((distance**2 + r2**2 - r1**2) / (2 * distance * r2))
            term3 = 0.5 * math.sqrt((-distance + r1 + r2) * (distance + r1 - r2) * (distance - r1 + r2) * (distance + r1 + r2))
            
            intersection_area = term1 + term2 - term3
            
            # 计算并集面积
            area1 = math.pi * r1**2
            area2 = math.pi * r2**2
            union_area = area1 + area2 - intersection_area
            
            # 返回交集与并集的比例（Jaccard系数）
            return intersection_area / union_area if union_area > 0 else 0.0
            
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def analyze_observation_compatibility(self, sensor1: SensorParameters, sensor2: SensorParameters) -> Dict[str, float]:
        """
        分析观测参数的兼容性
        
        返回:
            兼容性分析结果
        """
        params1 = set(sensor1.observation_parameters)
        params2 = set(sensor2.observation_parameters)
        
        # 计算参数重叠
        common_params = params1.intersection(params2)
        unique_params1 = params1 - params2
        unique_params2 = params2 - params1
        all_params = params1.union(params2)
        
        # 计算不同类型的兼容性
        similarity = len(common_params) / len(all_params) if all_params else 0.0
        complementarity = (len(unique_params1) + len(unique_params2)) / len(all_params) if all_params else 0.0
        
        # 机制兼容性
        mechanism_compatibility = 1.0 if sensor1.observation_mechanism != sensor2.observation_mechanism else 0.5
        
        return {
            'parameter_similarity': similarity,
            'parameter_complementarity': complementarity,
            'mechanism_compatibility': mechanism_compatibility,
            'common_parameters': list(common_params),
            'unique_parameters_sensor1': list(unique_params1),
            'unique_parameters_sensor2': list(unique_params2)
        }
    
    def evaluate_time_relationship(self, sensor1: SensorParameters, sensor2: SensorParameters) -> Tuple[TimeRelationType, str]:
        """
        评估时间关系（定性分析）
        
        返回:
            (关系类型, 详细说明)
        """
        # 检查时间是否重叠
        overlap_start = max(sensor1.start_time, sensor2.start_time)
        overlap_end = min(sensor1.end_time, sensor2.end_time)
        has_overlap = overlap_start < overlap_end
        
        # 检查观测参数相似性
        params1 = set(sensor1.observation_parameters)
        params2 = set(sensor2.observation_parameters)
        common_params = params1.intersection(params2)
        has_common_params = len(common_params) > 0
        
        # 判断完全重叠
        complete_overlap = (sensor1.start_time == sensor2.start_time and 
                          sensor1.end_time == sensor2.end_time)
        
        if has_overlap:
            if complete_overlap and has_common_params:
                # 时间完全重叠且有相同观测参数
                explanation = f"两传感器观测时间完全重叠({sensor1.start_time.strftime('%Y-%m-%d %H:%M')} 到 {sensor1.end_time.strftime('%Y-%m-%d %H:%M')})，且都观测{list(common_params)}参数，存在时间竞争。"
                return TimeRelationType.COMPETITIVE, explanation
            else:
                # 时间有重叠但不完全重叠，或参数不同
                if has_common_params:
                    explanation = f"两传感器观测时间部分重叠，都观测{list(common_params)}参数，可以互补观测以增强时间覆盖。"
                else:
                    explanation = f"两传感器观测时间有重叠，但观测参数不同（传感器1观测{list(params1)}，传感器2观测{list(params2)}），形成时间互补。"
                return TimeRelationType.COMPLEMENTARY, explanation
        else:
            # 时间无重叠
            explanation = f"两传感器观测时间无重叠（传感器1: {sensor1.start_time.strftime('%Y-%m-%d %H:%M')}-{sensor1.end_time.strftime('%Y-%m-%d %H:%M')}，传感器2: {sensor2.start_time.strftime('%Y-%m-%d %H:%M')}-{sensor2.end_time.strftime('%Y-%m-%d %H:%M')}），时间上相互独立。"
            return TimeRelationType.INDEPENDENT, explanation
    
    def evaluate_space_relationship(self, sensor1: SensorParameters, sensor2: SensorParameters) -> Tuple[SpaceRelationType, str]:
        """
        评估空间关系（定性分析）
        
        返回:
            (关系类型, 详细说明)
        """
        # 计算距离和空间关系
        distance = self.calculate_distance(
            sensor1.latitude, sensor1.longitude,
            sensor2.latitude, sensor2.longitude
        )
        
        # 检查覆盖范围
        total_radius = sensor1.coverage_radius + sensor2.coverage_radius
        has_overlap = distance < total_radius
        high_overlap = distance < min(sensor1.coverage_radius, sensor2.coverage_radius)
        
        # 检查观测参数和机制
        params1 = set(sensor1.observation_parameters)
        params2 = set(sensor2.observation_parameters)
        common_params = params1.intersection(params2)
        unique_params1 = params1 - params2
        unique_params2 = params2 - params1
        
        same_mechanism = sensor1.observation_mechanism == sensor2.observation_mechanism
        
        if has_overlap:
            if high_overlap:
                # 高度空间重叠
                if len(common_params) > 0 and same_mechanism:
                    # 空间竞争：完全重叠且观测相同参数，机制也相同
                    explanation = f"两传感器空间覆盖高度重叠（距离{distance:.1f}km < 覆盖半径{min(sensor1.coverage_radius, sensor2.coverage_radius):.1f}km），都使用{sensor1.observation_mechanism}观测{list(common_params)}，存在空间竞争。"
                    return SpaceRelationType.COMPETITIVE, explanation
                elif not same_mechanism:
                    # 空间增强：重叠但机制不同
                    explanation = f"两传感器空间覆盖重叠，但使用不同观测机制（传感器1: {sensor1.observation_mechanism}，传感器2: {sensor2.observation_mechanism}），可以提供空间增强观测。"
                    return SpaceRelationType.ENHANCED, explanation
                else:
                    # 空间互补：重叠但观测参数互补
                    explanation = f"两传感器空间覆盖重叠，观测参数互补（传感器1独有: {list(unique_params1)}，传感器2独有: {list(unique_params2)}），形成空间互补。"
                    return SpaceRelationType.COMPLEMENTARY, explanation
            else:
                # 部分空间重叠
                if len(unique_params1) > 0 or len(unique_params2) > 0:
                    explanation = f"两传感器空间部分重叠（距离{distance:.1f}km），观测不同参数，可以形成空间互补覆盖。"
                    return SpaceRelationType.COMPLEMENTARY, explanation
                else:
                    explanation = f"两传感器空间部分重叠，可以通过协同观测提供空间增强效果。"
                    return SpaceRelationType.ENHANCED, explanation
        else:
            # 空间无重叠
            explanation = f"两传感器空间无重叠（距离{distance:.1f}km > 总覆盖半径{total_radius:.1f}km），空间上相互独立。"
            return SpaceRelationType.INDEPENDENT, explanation
    
    def analyze_sensor_relationship(self, sensor1: SensorParameters, sensor2: SensorParameters) -> Dict:
        """
        分析两个传感器的时空关系（定性分析）
        
        返回:
            关系分析结果
        """
        # 时间关系分析
        time_relation, time_explanation = self.evaluate_time_relationship(sensor1, sensor2)
        
        # 空间关系分析
        space_relation, space_explanation = self.evaluate_space_relationship(sensor1, sensor2)
        
        return {
            'sensor1_id': sensor1.id,
            'sensor2_id': sensor2.id,
            'time_relationship': time_relation.value,
            'time_explanation': time_explanation,
            'space_relationship': space_relation.value,
            'space_explanation': space_explanation,
            'summary': f"时间关系: {time_relation.value}, 空间关系: {space_relation.value}"
        }
    
    def _generate_qualitative_recommendations(self, time_rel: TimeRelationType, space_rel: SpaceRelationType) -> List[str]:
        """生成定性关系建议"""
        recommendations = []
        
        # 时间维度建议
        if time_rel == TimeRelationType.COMPETITIVE:
            recommendations.append("时间竞争：建议调整观测时间避免重复，可采用轮流观测或分时段观测策略")
        elif time_rel == TimeRelationType.COMPLEMENTARY:
            recommendations.append("时间互补：建议协调观测时间，联合观测可获得更完整的时间序列数据")
        elif time_rel == TimeRelationType.INDEPENDENT:
            recommendations.append("时间独立：两传感器观测时间不冲突，可以独立运行")
        
        # 空间维度建议
        if space_rel == SpaceRelationType.COMPETITIVE:
            recommendations.append("空间竞争：建议重新规划部署位置以避免冗余覆盖，或者将其中一个传感器迁移到其他区域")
        elif space_rel == SpaceRelationType.COMPLEMENTARY:
            recommendations.append("空间互补：建议保持当前部署，两传感器可以形成良好的空间互补覆盖")
        elif space_rel == SpaceRelationType.ENHANCED:
            recommendations.append("空间增强：建议加强两传感器间的数据协调，可以通过数据融合提高观测质量")
        elif space_rel == SpaceRelationType.INDEPENDENT:
            recommendations.append("空间独立：两传感器覆盖区域不重叠，可以独立运行互不影响")
        
        # 综合建议
        if time_rel != TimeRelationType.INDEPENDENT or space_rel != SpaceRelationType.INDEPENDENT:
            recommendations.append("综合建议：两传感器存在时间或空间上的相互关系，建议制定协调运行方案")
        
        return recommendations

def demo_relationship_analysis():
    """传感器关系分析演示"""
    print("="*60)
    print("传感器时空关系分析演示")
    print("="*60)
    
    # 创建分析器
    analyzer = SensorRelationshipAnalyzer()
    
    # 创建测试传感器
    print("\n场景1: 时间竞争 + 空间竞争")
    sensor1_competitive = SensorParameters(
        id="Temp_Sensor_A",
        latitude=39.9042,
        longitude=116.4074,
        coverage_radius=10.0,
        start_time=datetime(2023, 7, 1, 8, 0),
        end_time=datetime(2023, 7, 1, 18, 0),
        observation_parameters=['temperature', 'humidity'],
        observation_mechanism='in_situ'
    )
    
    sensor2_competitive = SensorParameters(
        id="Temp_Sensor_B",
        latitude=39.9042,
        longitude=116.4074,
        coverage_radius=12.0,
        start_time=datetime(2023, 7, 1, 8, 0),
        end_time=datetime(2023, 7, 1, 18, 0),
        observation_parameters=['temperature', 'pressure'],
        observation_mechanism='in_situ'
    )
    
    result1 = analyzer.comprehensive_relationship_analysis(sensor1_competitive, sensor2_competitive)
    print_analysis_result(result1)
    
    print("\n" + "="*60)
    print("场景2: 时间互补 + 空间增强")
    sensor1_complementary = SensorParameters(
        id="Remote_Sensor_1",
        latitude=39.9042,
        longitude=116.4074,
        coverage_radius=15.0,
        start_time=datetime(2023, 7, 1, 6, 0),
        end_time=datetime(2023, 7, 1, 12, 0),
        observation_parameters=['temperature', 'NDVI'],
        observation_mechanism='remote_sensing'
    )
    
    sensor2_complementary = SensorParameters(
        id="Ground_Station_1",
        latitude=39.9100,
        longitude=116.4100,
        coverage_radius=5.0,
        start_time=datetime(2023, 7, 1, 12, 0),
        end_time=datetime(2023, 7, 1, 18, 0),
        observation_parameters=['temperature', 'humidity', 'soil_moisture'],
        observation_mechanism='in_situ'
    )
    
    result2 = analyzer.comprehensive_relationship_analysis(sensor1_complementary, sensor2_complementary)
    print_analysis_result(result2)
    
    print("\n" + "="*60)
    print("场景3: 多传感器关系矩阵")
    
    # 创建多个传感器
    sensors = [
        SensorParameters("S1", 39.90, 116.40, 8, datetime(2023,7,1,8,0), datetime(2023,7,1,16,0), ['temp'], 'in_situ'),
        SensorParameters("S2", 39.91, 116.41, 10, datetime(2023,7,1,10,0), datetime(2023,7,1,18,0), ['temp','humidity'], 'remote_sensing'),
        SensorParameters("S3", 39.92, 116.39, 12, datetime(2023,7,1,6,0), datetime(2023,7,1,14,0), ['pressure'], 'satellite'),
        SensorParameters("S4", 39.89, 116.42, 6, datetime(2023,7,1,14,0), datetime(2023,7,1,22,0), ['temp','soil'], 'in_situ')
    ]
    
    # 计算关系矩阵
    relationship_matrix = analyze_sensor_network(analyzer, sensors)
    visualize_relationship_matrix(relationship_matrix, sensors)

def print_analysis_result(result: Dict):
    """打印分析结果"""
    print(f"\n传感器关系分析: {result['sensor1_id']} vs {result['sensor2_id']}")
    print(f"总体评分: {result['overall_score']:.3f}")
    print(f"关系总结: {result['summary']}")
    
    print(f"\n时间关系:")
    time_rel = result['time_relationship']
    print(f"  类型: {time_rel['type']}")
    print(f"  强度: {time_rel['strength']:.3f}")
    print(f"  重叠时间: {time_rel['details']['overlap_duration']:.1f} 小时")
    print(f"  参数相似性: {time_rel['details']['compatibility']['parameter_similarity']:.3f}")
    
    print(f"\n空间关系:")
    space_rel = result['space_relationship']
    print(f"  类型: {space_rel['type']}")
    print(f"  强度: {space_rel['strength']:.3f}")
    print(f"  空间重叠: {space_rel['details']['space_overlap_ratio']:.3f}")
    print(f"  距离: {space_rel['details']['distance_km']:.1f} km")
    
    print(f"\n建议:")
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"  {i}. {rec}")

def analyze_sensor_network(analyzer: SensorRelationshipAnalyzer, sensors: List[SensorParameters]) -> np.ndarray:
    """分析传感器网络关系矩阵"""
    n = len(sensors)
    matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i+1, n):
            result = analyzer.comprehensive_relationship_analysis(sensors[i], sensors[j])
            matrix[i][j] = result['overall_score']
            matrix[j][i] = result['overall_score']  # 对称矩阵
    
    return matrix

def visualize_relationship_matrix(matrix: np.ndarray, sensors: List[SensorParameters]):
    """可视化关系矩阵"""
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # 绘制热力图
    im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')
    
    # 设置标签
    sensor_labels = [s.id for s in sensors]
    ax.set_xticks(range(len(sensors)))
    ax.set_yticks(range(len(sensors)))
    ax.set_xticklabels(sensor_labels)
    ax.set_yticklabels(sensor_labels)
    
    # 添加数值标注
    for i in range(len(sensors)):
        for j in range(len(sensors)):
            if i != j:
                text = ax.text(j, i, f'{matrix[i, j]:.2f}',
                             ha="center", va="center", color="black", fontsize=10)
    
    # 添加颜色条
    cbar = plt.colorbar(im)
    cbar.set_label('关系强度', rotation=270, labelpad=15)
    
    ax.set_title('传感器网络关系矩阵', fontsize=14, fontweight='bold')
    ax.set_xlabel('传感器')
    ax.set_ylabel('传感器')
    
    plt.tight_layout()
    plt.show()
    
    # 打印矩阵统计
    print("\n关系矩阵统计:")
    print(f"平均关系强度: {np.mean(matrix[matrix > 0]):.3f}")
    print(f"最强关系: {np.max(matrix):.3f}")
    print(f"关系总数: {np.sum(matrix > 0.1) // 2}")  # 除以2因为对称

def main():
    """主演示函数"""
    print("传感器时空关系分析系统")
    print("="*80)
    
    demo_relationship_analysis()
    
    print(f"\n" + "="*80)
    print("演示完成！")
    print("="*80)
    
    print(f"\n功能总结:")
    print(f"1. 时间关系评估 - 竞争/互补/独立关系识别")
    print(f"2. 空间关系评估 - 竞争/互补/增强/独立关系识别")
    print(f"3. 观测参数兼容性分析")
    print(f"4. 传感器网络关系矩阵可视化")
    print(f"5. 智能化部署建议生成")
    print(f"6. 支持多种观测机制和参数类型")

if __name__ == "__main__":
    main()