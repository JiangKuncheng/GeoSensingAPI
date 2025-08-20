# 🛰️ 对地观测规划四阶段工作流程实例

## 📋 规划框架说明

基于您的四阶段观测规划框架，我设计了完整的工作流程实例：

1. **任务/需求阶段** → 需求结构化 + 任务类型判断
2. **发现阶段** → 传感器初筛匹配
3. **评估阶段** → 定量性能评估  
4. **配置阶段** → 优化部署配置

---

## 🌊 实例1：海洋石油污染监测系统规划

### 第1阶段：任务/需求阶段

#### 第1.1步：需求结构化
```
用户原始需求：
"我们需要监测渤海湾地区的石油泄漏情况，要求能够及时发现污染并跟踪扩散"

结构化需求：
{
  "监测目标": "石油污染",
  "监测区域": "渤海湾海域",
  "时间要求": "实时监测",
  <!-- "空间分辨率": "≤100m", -->提取不出来
  <!-- "时间分辨率": "≤6小时", -->提取不出来
  "覆盖要求": "90%海域覆盖",
  "响应时间": "≤2小时发现",
  "监测参数": ["石油膜厚度", "污染范围", "扩散方向"]
}
```

#### 第1.2步：任务类型判断
**任务类型**: **配置任务** (需要建立全新的监测网络)

### 第2阶段：发现阶段

#### 使用工具组合进行传感器初筛：

```python
# 工具1: 获取监测海域边界
from satelliteTool.getPlaceBoundary import get_boundary
target_area = get_boundary("渤海湾")

# 工具2: 基于需求匹配候选传感器
candidate_satellites = [
    {"name": "SENTINEL-1", "type": "SAR", "resolution": "10m", "revisit": "6天"},
    {"name": "SENTINEL-2", "type": "光学", "resolution": "10m", "revisit": "5天"},
    {"name": "LANDSAT-8", "type": "光学", "resolution": "30m", "revisit": "16天"},
    {"name": "GF-3", "type": "SAR", "resolution": "1-500m", "revisit": "29天"}
]

candidate_ground_sensors = [
    {"type": "海上浮标", "range": "5km", "parameters": ["油膜", "水质"]},
    {"type": "岸基雷达", "range": "50km", "parameters": ["目标检测"]},
    {"type": "无人船", "range": "移动", "parameters": ["水质采样", "图像"]}
]

# 初筛条件匹配
qualified_satellites = filter_by_requirements(
    candidates=candidate_satellites,
    min_resolution=100,  # ≤100m
    max_revisit_hours=144  # ≤6天
)
```

### 第3阶段：评估阶段

#### 使用定量工具评估传感器性能：

```python
# 工具3: 卫星覆盖足迹分析
from satelliteTool.get_satellite_footprint import get_satellite_footprint

# 评估卫星覆盖能力
satellite_coverage = {}
for satellite in qualified_satellites:
    coverage = get_satellite_footprint(
        satellite_name=satellite["name"],
        target_area=target_area,
        time_range="30天",
        cloud_threshold=0.3
    )
    satellite_coverage[satellite["name"]] = coverage

# 工具4: 地面传感器覆盖分析
from GeoPandasTool.buffer import buffer
from GeoPandasTool.union import union

# 评估地面传感器网络覆盖
sensor_positions = [(117.2, 39.1), (118.5, 38.8), (119.1, 39.3)]  # 候选位置
ground_coverage = []
for pos in sensor_positions:
    sensor_area = buffer(
        geojson_point(pos), 
        distance=5000  # 5km监测半径
    )
    ground_coverage.append(sensor_area)

total_ground_coverage = union(*ground_coverage)

# 工具5: 覆盖率计算
from GeoPandasTool.intersection import intersection
from GeoPandasTool.area import area

coverage_intersection = intersection(total_ground_coverage, target_area)
coverage_ratio = area(coverage_intersection) / area(target_area)

print(f"地面传感器覆盖率: {coverage_ratio*100:.1f}%")
```

### 第4阶段：配置阶段

#### 使用优化算法进行网络配置：

```python
# 工具6: 混合传感器网络优化
from deploy.hybrid_sensor_from_scratch import HybridSensorFromScratchOptimizer

# 配置混合监测网络
optimizer = HybridSensorFromScratchOptimizer(
    target_area=target_area,
    satellites=qualified_satellites,
    ground_sensors=candidate_ground_sensors,
    constraints={
        "target_coverage_ratio": 0.90,
        "max_satellites": 3,
        "max_ground_sensors": 15,
        "max_cost": 500000,
        "response_time": 2  # 2小时响应要求
    }
)

# 执行优化
optimal_solution = optimizer.optimize_genetic(generations=50)

# 工具7: 传感器关系分析
from deploy.sensor_relationship_analyzer import SensorRelationshipAnalyzer

analyzer = SensorRelationshipAnalyzer()
sensor_relationships = analyzer.analyze_sensor_network(
    selected_sensors=optimal_solution.selected_sensors
)

# 最终配置验证
if optimal_solution.coverage_ratio >= 0.90:
    print("✅ 配置成功：满足90%覆盖率要求")
    export_deployment_plan(optimal_solution)
else:
    print("❌ 需要进一步优化配置")
```

---

## 🔥 实例2：森林火灾预警系统规划

### 第1阶段：任务/需求阶段

#### 第1.1步：需求结构化
```
用户原始需求：
"大兴安岭林区需要建立火灾预警系统，要求能提前2小时预警"

结构化需求：
{
  "监测目标": "森林火灾",
  "监测区域": "大兴安岭林区",
  "预警时间": "提前2小时",
  "监测参数": ["温度异常", "烟雾", "热点"],
  "覆盖要求": "重点林区100%",
  "误警率": "≤5%",
  "检测精度": "火点±50m"
}
```

#### 第1.2步：任务类型判断
**任务类型**: **发现任务** + **配置任务** (需要发现火灾风险点并配置预警网络)

### 第2阶段：发现阶段

```python
# 工具组合：风险区域发现
from satelliteTool.getPlaceBoundary import get_boundary
from GeoPandasTool.buffer import buffer
from GeoPandasTool.difference import difference

# 获取林区边界
forest_area = get_boundary("大兴安岭国家森林公园")

# 排除低风险区域（湿地、水体）
water_bodies = get_boundary("林区水系")
wetlands = get_boundary("湿地保护区")
low_risk_areas = union(water_bodies, wetlands)

# 发现高风险火灾区域
high_risk_zones = difference(forest_area, low_risk_areas)

# 历史火点数据分析
historical_fire_points = load_fire_history_data("2010-2023")
fire_risk_buffer = [buffer(point, 2000) for point in historical_fire_points]
high_risk_areas = union(*fire_risk_buffer)
```

### 第3阶段：评估阶段

```python
# 工具组合：多源传感器评估
from deploy.sensor_relationship_analyzer import SensorRelationshipAnalyzer

# 候选传感器性能评估
candidate_sensors = {
    "卫星传感器": [
        {"name": "MODIS", "火点检测": "1km", "重访": "1天2次"},
        {"name": "VIIRS", "火点检测": "375m", "重访": "1天2次"},
        {"name": "SENTINEL-2", "热异常": "20m", "重访": "5天"}
    ],
    "地面传感器": [
        {"type": "热红外相机", "range": "5km", "accuracy": "±2°C"},
        {"type": "烟雾传感器", "range": "1km", "response": "30秒"},
        {"type": "气象站", "range": "10km", "parameters": ["风速", "湿度"]}
    ]
}

# 评估传感器时空协调性
analyzer = SensorRelationshipAnalyzer()
for sat in candidate_sensors["卫星传感器"]:
    for ground in candidate_sensors["地面传感器"]:
        relationship = analyzer.analyze_sensor_relationship(
            sensor1=sat, sensor2=ground
        )
        print(f"{sat['name']} + {ground['type']}: {relationship['综合评分']}")
```

### 第4阶段：配置阶段

```python
# 工具组合：预警网络配置
from deploy.ground_sensor_from_scratch import GroundSensorFromScratchSolver
from deploy.hybrid_sensor_addition_optimize import HybridSensorAdditionOptimizer

# 第一步：地面传感器网络布设
ground_solver = GroundSensorFromScratchSolver(
    target_area_coords=high_risk_zones,
    coverage_ratio=0.95,
    sensor_radius=3000,  # 3km监测半径
    grid_resolution=500
)

ground_sensors = ground_solver.solve()

# 第二步：卫星监测补充
hybrid_optimizer = HybridSensorAdditionOptimizer(
    target_area=forest_area
)

# 基于地面网络增补卫星监测
final_solution = hybrid_optimizer.optimize_additions_greedy(
    existing_ground_sensors=ground_sensors,
    target_coverage=1.0,  # 100%覆盖重点区域
    satellite_types=["MODIS", "VIIRS"]
)

# 预警时效性验证
warning_time = calculate_warning_lead_time(
    detection_sensors=final_solution.sensors,
    fire_spread_model="Canadian Forest Fire Weather Index"
)

if warning_time >= 2:  # 满足2小时提前预警
    print("✅ 预警系统配置成功")
else:
    print("❌ 需要增加传感器密度")
```

---

## 🌾 实例3：精准农业监测配置

### 第1阶段：任务/需求阶段

#### 第1.1步：需求结构化
```
用户原始需求：
"我们有1000公顷玉米地，想实现精准灌溉和病虫害监测"

结构化需求：
{
  "监测目标": "作物长势+病虫害+土壤状况",
  "农田面积": "1000公顷",
  "作物类型": "玉米",
  "监测周期": "生长季全程",
  "精度要求": "地块级(10m精度)",
  "决策支持": "灌溉时机+病虫害防治"
}
```

#### 第1.2步：任务类型判断
**任务类型**: **评估任务** + **配置任务** (评估现有条件并配置监测网络)

### 第2阶段：发现阶段

```python
# 工具组合：农田区域分析
from GeoPandasTool.area import area
from GeoPandasTool.centroid import centroid

# 农田地块分析
farm_boundary = load_farm_boundary("玉米种植区")
field_polygons = split_into_management_units(farm_boundary, unit_size=10)  # 10公顷管理单元

# 发现适合的监测技术
monitoring_technologies = {
    "卫星遥感": {
        "NDVI监测": ["SENTINEL-2", "LANDSAT-8"],
        "热红外": ["LANDSAT-8", "MODIS"],
        "高分辨率": ["WorldView", "GeoEye"]
    },
    "地面传感器": {
        "土壤": ["湿度传感器", "温度传感器", "养分传感器"],
        "气象": ["小气候站", "雨量计"],
        "作物": ["冠层监测器", "果实监测器"]
    },
    "无人机": {
        "可见光": "作物长势评估",
        "多光谱": "病虫害检测",
        "热红外": "水分胁迫监测"
    }
}
```

### 第3阶段：评估阶段

```python
# 工具组合：技术适用性评估
from satelliteTool.get_satellite_footprint import get_satellite_footprint

# 评估卫星覆盖时效
for satellite in ["SENTINEL-2", "LANDSAT-8"]:
    coverage_schedule = get_satellite_footprint(
        satellite_name=satellite,
        target_area=farm_boundary,
        time_range="玉米生长季6个月",
        cloud_threshold=0.2
    )
    
    effective_observations = filter_clear_sky_observations(coverage_schedule)
    temporal_resolution = calculate_average_revisit(effective_observations)
    
    print(f"{satellite} 有效观测频率: {temporal_resolution}天")

# 评估地面传感器网络需求
field_centroids = [centroid(field) for field in field_polygons]
sensor_network_cost = estimate_sensor_network_cost(
    locations=field_centroids,
    sensor_types=["土壤湿度", "气象"],
    communication="LoRa无线"
)

# 评估监测精度vs成本
precision_cost_analysis = evaluate_monitoring_options(
    satellite_option={"cost": 50000, "precision": "10m", "frequency": "5天"},
    drone_option={"cost": 100000, "precision": "5cm", "frequency": "按需"},
    ground_option={"cost": 150000, "precision": "点测量", "frequency": "实时"}
)
```

### 第4阶段：配置阶段

```python
# 工具组合：精准农业系统配置
from deploy.ground_sensor_position_optimize import GroundSensorPositionOptimizer

# 第一步：土壤传感器网络优化
soil_optimizer = GroundSensorPositionOptimizer(
    target_area_coords=farm_boundary,
    sensor_radius=500,  # 500m代表性范围
    grid_resolution=100
)

# 基于土壤类型分区优化传感器位置
soil_types = classify_soil_zones(farm_boundary)
optimized_soil_sensors = []

for zone in soil_types:
    zone_sensors = soil_optimizer.optimize_positions(
        target_area=zone,
        sensor_count=calculate_sensor_need(zone),
        optimization_target="土壤代表性"
    )
    optimized_soil_sensors.extend(zone_sensors)

# 第二步：多尺度监测体系集成
from deploy.hybrid_sensor_from_scratch import HybridSensorFromScratchOptimizer

integrated_system = HybridSensorFromScratchOptimizer(
    target_area=farm_boundary,
    satellites=["SENTINEL-2", "LANDSAT-8"],
    ground_sensors=optimized_soil_sensors,
    constraints={
        "monitoring_frequency": "周级",
        "spatial_resolution": "管理单元级",
        "cost_budget": 200000,
        "automation_level": "高度自动化"
    }
)

final_monitoring_system = integrated_system.optimize_genetic(
    optimization_objectives=["监测精度", "成本效益", "决策及时性"]
)

# 第三步：决策支持系统配置
decision_support_config = configure_decision_system(
    monitoring_system=final_monitoring_system,
    crop_model="玉米生长模型",
    irrigation_system="精准滴灌",
    pest_management="IPM综合防治"
)

print("✅ 精准农业监测系统配置完成")
```

---

## 🔧 各实例四阶段工具使用流程详解

### 🌊 实例1：海洋石油污染监测系统规划

#### 第1阶段：任务/需求阶段
**使用工具**: 无需特定工具
- 需求结构化处理
- 任务类型判断 → **配置任务**

#### 第2阶段：发现阶段
**使用工具流程**:
1. **satelliteTool/getPlaceBoundary.py** → 获取渤海湾边界
2. 传感器候选库匹配 → 筛选符合分辨率要求的卫星

#### 第3阶段：评估阶段  
**使用工具流程**:
1. **satelliteTool/get_satellite_footprint.py** → 评估各卫星覆盖能力
2. **GeoPandasTool/buffer.py** → 创建地面传感器覆盖圆
3. **GeoPandasTool/union.py** → 合并地面传感器覆盖区域
4. **GeoPandasTool/intersection.py** → 计算与目标区域交集
5. **GeoPandasTool/area.py** → 计算覆盖率

#### 第4阶段：配置阶段
**使用工具流程**:
1. **deploy/hybrid_sensor_from_scratch.py** → 混合传感器网络优化
2. **deploy/sensor_relationship_analyzer.py** → 传感器协调分析

---

### 🔥 实例2：森林火灾预警系统规划

#### 第1阶段：任务/需求阶段
**使用工具**: 无需特定工具
- 需求结构化处理
- 任务类型判断 → **发现任务** + **配置任务**

#### 第2阶段：发现阶段
**使用工具流程**:
1. **satelliteTool/getPlaceBoundary.py** → 获取大兴安岭林区边界
2. **satelliteTool/getPlaceBoundary.py** → 获取水系和湿地边界
3. **GeoPandasTool/union.py** → 合并低风险区域
4. **GeoPandasTool/difference.py** → 排除低风险区域，得到高风险区域
5. **GeoPandasTool/buffer.py** → 基于历史火点创建风险缓冲区

#### 第3阶段：评估阶段
**使用工具流程**:
1. **deploy/sensor_relationship_analyzer.py** → 评估卫星与地面传感器协调性
2. 多传感器性能对比分析

#### 第4阶段：配置阶段
**使用工具流程**:
1. **deploy/ground_sensor_from_scratch.py** → 地面传感器网络布设
2. **deploy/hybrid_sensor_addition_optimize.py** → 在地面网络基础上增补卫星监测

---

### 🌾 实例3：精准农业监测配置

#### 第1阶段：任务/需求阶段
**使用工具**: 无需特定工具
- 需求结构化处理
- 任务类型判断 → **评估任务** + **配置任务**

#### 第2阶段：发现阶段
**使用工具流程**:
1. **GeoPandasTool/area.py** → 计算各农田地块面积
2. **GeoPandasTool/centroid.py** → 确定各地块中心点
3. 适用监测技术发现和匹配

#### 第3阶段：评估阶段
**使用工具流程**:
1. **satelliteTool/get_satellite_footprint.py** → 评估SENTINEL-2和LANDSAT-8覆盖时效
2. **GeoPandasTool/centroid.py** → 确定传感器网络节点位置
3. 成本效益分析

#### 第4阶段：配置阶段
**使用工具流程**:
1. **deploy/ground_sensor_position_optimize.py** → 土壤传感器网络优化
2. **deploy/hybrid_sensor_from_scratch.py** → 多尺度监测体系集成
3. 决策支持系统配置

---

## 📊 工具使用对比分析

### 🎯 各实例工具使用统计

| 工具名称 | 实例1(海洋污染) | 实例2(森林火灾) | 实例3(精准农业) |
|---------|----------------|----------------|----------------|
| **getPlaceBoundary** | ✅ 第2阶段 | ✅ 第2阶段(多次) | ❌ |
| **buffer** | ✅ 第3阶段 | ✅ 第2阶段 | ❌ |
| **union** | ✅ 第3阶段 | ✅ 第2阶段 | ❌ |
| **difference** | ❌ | ✅ 第2阶段 | ❌ |
| **intersection** | ✅ 第3阶段 | ❌ | ❌ |
| **area** | ✅ 第3阶段 | ❌ | ✅ 第2阶段 |
| **centroid** | ❌ | ❌ | ✅ 第2、3阶段 |
| **get_satellite_footprint** | ✅ 第3阶段 | ❌ | ✅ 第3阶段 |
| **sensor_relationship_analyzer** | ✅ 第4阶段 | ✅ 第3阶段 | ❌ |
| **hybrid_sensor_from_scratch** | ✅ 第4阶段 | ❌ | ✅ 第4阶段 |
| **ground_sensor_from_scratch** | ❌ | ✅ 第4阶段 | ❌ |
| **position_optimize** | ❌ | ❌ | ✅ 第4阶段 |
| **addition_optimize** | ❌ | ✅ 第4阶段 | ❌ |

### 🔄 工具使用模式识别

#### 模式A：空间分析密集型（海洋污染）
```
getPlaceBoundary → buffer → union → intersection → area → hybrid_from_scratch
```

#### 模式B：区域发现导向型（森林火灾）
```
getPlaceBoundary(多次) → union → difference → buffer → ground_from_scratch → addition_optimize
```

#### 模式C：位置优化导向型（精准农业）
```
area → centroid → get_satellite_footprint → position_optimize → hybrid_from_scratch
```

这个详细的工具使用流程为您的观测规划Agent提供了具体的操作指南。
