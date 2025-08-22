"""
简化的传感器时空关系分析器

只进行定性的关系评估，不包含复杂的量化计算和建议系统
"""

import math
from datetime import datetime
from typing import Tuple, Dict
from dataclasses import dataclass
from enum import Enum

class TimeRelation(Enum):
    """时间关系类型"""
    COMPETITIVE = "时间竞争"
    COMPLEMENTARY = "时间互补"
    ENHANCED = "时间增强"

class SpaceRelation(Enum):
    """空间关系类型"""
    COMPETITIVE = "空间竞争"
    COMPLEMENTARY = "空间互补"
    ENHANCED = "空间增强"

@dataclass
class Sensor:
    """传感器参数"""
    id: str
    # 空间参数
    latitude: float
    longitude: float
    coverage_radius: float  # 覆盖半径（km）
    
    # 时间参数
    start_time: datetime
    end_time: datetime
    
    # 观测参数
    observation_parameters: list  # 如 ['temperature', 'humidity']
    observation_mechanism: str   # 如 'remote_sensing', 'in_situ', 'satellite'

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """计算两点间距离（公里）"""
    R = 6371  # 地球半径
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def evaluate_time_relationship(sensor1: Sensor, sensor2: Sensor) -> Tuple[TimeRelation, str]:
    """
    评估时间关系
    
    返回: (关系类型, 详细说明)
    """
    # 检查时间重叠
    overlap_start = max(sensor1.start_time, sensor2.start_time)
    overlap_end = min(sensor1.end_time, sensor2.end_time)
    has_overlap = overlap_start < overlap_end
    
    # 检查观测参数
    params1 = set(sensor1.observation_parameters)
    params2 = set(sensor2.observation_parameters)
    common_params = params1.intersection(params2)
    unique_params1 = params1 - params2
    unique_params2 = params2 - params1
    
    # 检查观测机制
    same_mechanism = sensor1.observation_mechanism == sensor2.observation_mechanism
    
    if has_overlap:
        if len(common_params) > 0 and same_mechanism:
            # 时间竞争：时间重叠，观测相同参数，使用相同机制
            explanation = f"两传感器观测时间重叠，都使用{sensor1.observation_mechanism}观测{list(common_params)}参数，存在时间竞争。"
            return TimeRelation.COMPETITIVE, explanation
        elif not same_mechanism:
            # 时间增强：时间重叠，但使用不同观测机制
            explanation = f"两传感器观测时间重叠，但使用不同观测机制（{sensor1.observation_mechanism} vs {sensor2.observation_mechanism}），可以提供时间增强观测。"
            return TimeRelation.ENHANCED, explanation
        else:
            # 时间互补：时间重叠，但观测参数不同或部分重叠
            explanation = f"两传感器观测时间重叠，观测参数互补（传感器1独有: {list(unique_params1)}，传感器2独有: {list(unique_params2)}），形成时间互补。"
            return TimeRelation.COMPLEMENTARY, explanation
    else:
        # 时间不重叠时，根据观测参数判断关系类型
        if len(common_params) > 0:
            explanation = f"两传感器观测时间不重叠但观测相同参数{list(common_params)}，形成时间互补覆盖。"
            return TimeRelation.COMPLEMENTARY, explanation
        else:
            explanation = f"两传感器观测时间不重叠且观测不同参数，可以提供时间增强的综合观测。"
            return TimeRelation.ENHANCED, explanation

def evaluate_space_relationship(sensor1: Sensor, sensor2: Sensor) -> Tuple[SpaceRelation, str]:
    """
    评估空间关系
    
    返回: (关系类型, 详细说明)
    """
    # 计算距离
    distance = calculate_distance(
        sensor1.latitude, sensor1.longitude,
        sensor2.latitude, sensor2.longitude
    )
    
    # 检查覆盖重叠
    total_radius = sensor1.coverage_radius + sensor2.coverage_radius
    has_overlap = distance < total_radius
    
    # 检查观测参数和机制
    params1 = set(sensor1.observation_parameters)
    params2 = set(sensor2.observation_parameters)
    common_params = params1.intersection(params2)
    unique_params1 = params1 - params2
    unique_params2 = params2 - params1
    same_mechanism = sensor1.observation_mechanism == sensor2.observation_mechanism
    
    if has_overlap:
        # 有空间重叠
        if len(common_params) > 0 and same_mechanism:
            # 空间竞争：重叠且观测相同参数，使用相同机制
            explanation = f"两传感器空间重叠（距离{distance:.1f}km），都使用{sensor1.observation_mechanism}观测{list(common_params)}，存在空间竞争。"
            return SpaceRelation.COMPETITIVE, explanation
        elif not same_mechanism:
            # 空间增强：重叠但使用不同观测机制
            explanation = f"两传感器空间重叠，但使用不同观测机制（{sensor1.observation_mechanism} vs {sensor2.observation_mechanism}），可以提供空间增强观测。"
            return SpaceRelation.ENHANCED, explanation
        else:
            # 空间互补：重叠但观测参数不同
            explanation = f"两传感器空间重叠，观测参数互补（传感器1独有: {list(unique_params1)}，传感器2独有: {list(unique_params2)}），形成空间互补。"
            return SpaceRelation.COMPLEMENTARY, explanation
    else:
        # 无空间重叠
        if len(common_params) > 0:
            # 观测相同参数但空间不重叠，形成互补覆盖
            explanation = f"两传感器空间不重叠（距离{distance:.1f}km）但观测相同参数{list(common_params)}，形成空间互补覆盖。"
            return SpaceRelation.COMPLEMENTARY, explanation
        else:
            # 观测不同参数且空间不重叠，提供增强观测
            explanation = f"两传感器空间不重叠且观测不同参数，可以提供空间增强的综合观测覆盖。"
            return SpaceRelation.ENHANCED, explanation

def analyze_sensor_relationship(sensor1: Sensor, sensor2: Sensor) -> Dict:
    """
    分析两个传感器的时空关系
    
    参数:
        sensor1: 传感器1
        sensor2: 传感器2
    
    返回:
        关系分析结果字典
    """
    # 时间关系分析
    time_relation, time_explanation = evaluate_time_relationship(sensor1, sensor2)
    
    # 空间关系分析
    space_relation, space_explanation = evaluate_space_relationship(sensor1, sensor2)
    
    return {
        'sensor1_id': sensor1.id,
        'sensor2_id': sensor2.id,
        'time_relationship': time_relation.value,
        'time_explanation': time_explanation,
        'space_relationship': space_relation.value,
        'space_explanation': space_explanation,
        'summary': f"时间关系: {time_relation.value}，空间关系: {space_relation.value}"
    }

def demo_examples():
    """演示示例"""
    print("传感器时空关系分析演示")
    print("="*50)
    
    # 示例1: 时间竞争 + 空间竞争
    print("\n示例1: 时间竞争 + 空间竞争")
    sensor1 = Sensor(
        id="温度传感器A",
        latitude=39.9042, longitude=116.4074, coverage_radius=10,
        start_time=datetime(2023, 7, 1, 8, 0),
        end_time=datetime(2023, 7, 1, 18, 0),
        observation_parameters=['temperature', 'humidity'],
        observation_mechanism='in_situ'
    )
    
    sensor2 = Sensor(
        id="温度传感器B",
        latitude=39.9042, longitude=116.4074, coverage_radius=12,
        start_time=datetime(2023, 7, 1, 8, 0),
        end_time=datetime(2023, 7, 1, 18, 0),
        observation_parameters=['temperature'],
        observation_mechanism='in_situ'
    )
    
    result1 = analyze_sensor_relationship(sensor1, sensor2)
    print_result(result1)
    
    # 示例2: 时间互补 + 空间增强
    print("\n" + "="*50)
    print("示例2: 时间互补 + 空间增强")
    sensor3 = Sensor(
        id="遥感卫星",
        latitude=39.9042, longitude=116.4074, coverage_radius=15,
        start_time=datetime(2023, 7, 1, 6, 0),
        end_time=datetime(2023, 7, 1, 12, 0),
        observation_parameters=['temperature', 'NDVI'],
        observation_mechanism='remote_sensing'
    )
    
    sensor4 = Sensor(
        id="地面站",
        latitude=39.9100, longitude=116.4100, coverage_radius=5,
        start_time=datetime(2023, 7, 1, 12, 0),
        end_time=datetime(2023, 7, 1, 18, 0),
        observation_parameters=['temperature', 'soil_moisture'],
        observation_mechanism='in_situ'
    )
    
    result2 = analyze_sensor_relationship(sensor3, sensor4)
    print_result(result2)
    
    # 示例3: 时间互补 + 空间互补
    print("\n" + "="*50)
    print("示例3: 时间互补 + 空间互补")
    sensor5 = Sensor(
        id="北京温度传感器",
        latitude=39.9042, longitude=116.4074, coverage_radius=8,
        start_time=datetime(2023, 7, 1, 8, 0),
        end_time=datetime(2023, 7, 1, 16, 0),
        observation_parameters=['temperature'],
        observation_mechanism='in_situ'
    )
    
    sensor6 = Sensor(
        id="上海温度传感器",
        latitude=31.2304, longitude=121.4737, coverage_radius=8,
        start_time=datetime(2023, 7, 2, 8, 0),
        end_time=datetime(2023, 7, 2, 16, 0),
        observation_parameters=['temperature'],
        observation_mechanism='in_situ'
    )
    
    result3 = analyze_sensor_relationship(sensor5, sensor6)
    print_result(result3)

def print_result(result: Dict):
    """打印分析结果"""
    print(f"\n传感器: {result['sensor1_id']} vs {result['sensor2_id']}")
    print(f"时间关系: {result['time_relationship']}")
    print(f"  说明: {result['time_explanation']}")
    print(f"空间关系: {result['space_relationship']}")
    print(f"  说明: {result['space_explanation']}")
    print(f"总结: {result['summary']}")

if __name__ == "__main__":
    demo_examples()