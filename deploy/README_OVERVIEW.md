# GeoSensingAPI Deploy 目录总览

## 📁 目录结构和功能说明

`deploy/` 目录包含了完整的地面观测站和传感器网络优化解决方案，采用**六个独立功能文件**的模块化设计，涵盖从基础MCLP问题到高级混合传感器网络的各种应用场景。

### 🎯 六个核心功能模块

#### 🏠 **地面传感器优化系列** (3个文件)

##### 1. **地面传感器从零布设**
- **文件**: `ground_sensor_from_scratch.py`
- **功能**: 从零开始设计地面观测站网络
- **算法**: 贪心算法 + 网格离散化
- **特色**: 最大覆盖位置问题(MCLP)求解，纯地面传感器布设

##### 2. **地面传感器位置优化**
- **文件**: `ground_sensor_position_optimize.py`
- **功能**: 优化现有地面传感器位置（不增加数量）
- **算法**: 局部搜索 + 迭代优化
- **特色**: 固定传感器数量，重新配置位置提升覆盖率

##### 3. **地面传感器增补优化**
- **文件**: `ground_sensor_addition_optimize.py`
- **功能**: 通过最少增补地面传感器达到目标覆盖率
- **算法**: 贪心策略 + 覆盖缺口分析
- **特色**: 成本效益分析，智能选择增补位置

#### 🛰️ **混合传感器优化系列** (3个文件)

##### 4. **混合传感器从零布设**
- **文件**: `hybrid_sensor_from_scratch.py`
- **功能**: 从零开始设计卫星+地面混合传感器网络
- **算法**: 遗传算法(GA) + 多目标优化
- **特色**: 卫星轨道覆盖+地面圆形覆盖，资源约束优化

##### 5. **混合传感器位置优化**
- **文件**: `hybrid_sensor_position_optimize.py`
- **功能**: 优化现有卫星+地面传感器配置（不增加数量）
- **算法**: 遗传算法 + 模拟退火
- **特色**: 同步优化卫星轨道参数和地面传感器位置

##### 6. **混合传感器增补优化**
- **文件**: `hybrid_sensor_addition_optimize.py`
- **功能**: 智能增补卫星或地面传感器达到目标覆盖率
- **算法**: 贪心策略 + 传感器类型决策
- **特色**: 卫星vs地面传感器增补决策，成本效益最优化

### 📁 **演示目录**
- **目录**: `demos/`
- **内容**: 所有演示和测试文件
  - `mclp_examples.py` - 地面传感器示例演示
  - `optimization_demo.py` - 各种优化策略演示
  - `advanced_optimization_demo.py` - 高级算法演示

### 🔬 **分析工具模块**

#### 7. **传感器关系分析器**
- **文件**: `sensor_relationship_analyzer.py`
- **功能**: 分析传感器间的时空关系和协同效应
- **特色**: 时间竞争/互补分析、空间关系评估

#### 8. **简单传感器分析器**
- **文件**: `simple_sensor_analyzer.py`
- **功能**: 轻量级传感器关系分析工具
- **特色**: 快速分析、基础关系评估

### 🗂️ **辅助文件**
- `advanced_sensor_optimization.py` - 共享的传感器类定义和基础算法
- `README_OVERVIEW.md` - 本总览文档
- `README.md` - 详细技术文档

---

## 🚀 快速开始指南

### 环境要求

```bash
pip install numpy matplotlib shapely geopandas
```

### 🚀 超级简单演示 (30秒)

```bash
cd deploy
python run_demo.py
```
然后选择对应的功能编号即可！

### 1️⃣ 地面传感器功能演示

```python
# 从零布设
from ground_sensor_from_scratch import demo_ground_sensor_from_scratch
demo_ground_sensor_from_scratch()

# 位置优化
from ground_sensor_position_optimize import demo_ground_sensor_position_optimize  
demo_ground_sensor_position_optimize()

# 增补优化
from ground_sensor_addition_optimize import demo_ground_sensor_addition_optimize
demo_ground_sensor_addition_optimize()
```

### 2️⃣ 混合传感器功能演示

```python
# 从零布设
from hybrid_sensor_from_scratch import demo_hybrid_sensor_from_scratch
demo_hybrid_sensor_from_scratch()

# 位置优化
from hybrid_sensor_position_optimize import demo_hybrid_sensor_position_optimize
demo_hybrid_sensor_position_optimize()

# 增补优化  
from hybrid_sensor_addition_optimize import demo_hybrid_sensor_addition_optimize
demo_hybrid_sensor_addition_optimize()
```

### 3️⃣ 演示集合

```bash
# 地面传感器示例
python demos/mclp_examples.py

# 优化策略对比
python demos/optimization_demo.py

# 高级算法演示
python demos/advanced_optimization_demo.py
```

### 4️⃣ 传感器关系分析演示

```python
from sensor_relationship_analyzer import demo_relationship_analysis
demo_relationship_analysis()
```

---

## 📊 典型应用场景

### 🏢 场景1: 城市监测网络规划
```python
# 使用MCLP求解器进行基础规划
from mclp_observation_station import MCLPObservationStationSolver

# 定义城市区域
city_area = [(0, 0), (20, 0), (20, 15), (0, 15)]
solver = MCLPObservationStationSolver(city_area, 0.85, 3.0)
stations, count, coverage = solver.solve()
solver.visualize()
```

### 🛰️ 场景2: 卫星-地面协同网络
```python
# 使用高级优化器进行混合传感器选择
from advanced_sensor_optimization import demo_genetic_algorithm

# 一键演示遗传算法优化
ga_optimizer, solution = demo_genetic_algorithm()
```

### 🔧 场景3: 现有网络升级优化
```python
# 优化现有传感器位置
from optimize_existing_deployment import ExistingDeploymentOptimizer
from shapely.geometry import Polygon

target_area = Polygon([(0, 0), (12, 0), (12, 10), (0, 10)])
optimizer = ExistingDeploymentOptimizer(target_area)

# 假设现有传感器位置
existing_satellites = [...]  # 现有卫星配置
existing_sensors = [...]     # 现有地面传感器

# 优化位置
solution = optimizer.optimize_positions_genetic(
    existing_satellites, existing_sensors
)
optimizer.visualize_optimization_result(solution)
```

### 💰 场景4: 预算约束下的增补规划
```python
# 最少成本增补传感器
from optimize_with_additions import AdditionOptimizer

optimizer = AdditionOptimizer(target_area)
solution = optimizer.optimize_additions_greedy(
    existing_satellites, existing_sensors,
    target_coverage=0.9, max_budget=200
)
optimizer.visualize_addition_result(solution)
```

---

## 🎯 核心功能对比表

| 功能模块 | 主要算法 | 适用场景 | 计算复杂度 | 结果质量 |
|---------|---------|----------|-----------|----------|
| **MCLP基础求解** | 贪心算法 | 新建网络规划 | 低 | 中等 |
| **位置优化** | GA + SA | 现有网络调优 | 中等 | 高 |
| **增补优化** | 贪心 + GA | 网络扩展 | 中等 | 高 |
| **启发式优化** | GA + SA | 大规模复杂网络 | 高 | 很高 |
| **关系分析** | 数学模型 | 网络分析评估 | 低 | 高 |

---

## 📈 性能基准测试

### 测试场景规模
- **小规模**: 10×10区域, 4-6个传感器候选
- **中规模**: 15×12区域, 8-12个传感器候选  
- **大规模**: 20×15区域, 15-20个传感器候选

### 典型性能指标
```
算法类型          计算时间(s)    覆盖率(%)    成本效益
MCLP贪心算法      0.5-2.0       75-85       中等
遗传算法          2.0-10.0      85-95       高
模拟退火          1.0-5.0       80-90       高
混合优化          3.0-15.0      90-98       很高
```

---

## 🛠️ 自定义开发指南

### 扩展新的优化算法
```python
# 继承基础优化器类
from advanced_sensor_optimization import SensorNetworkOptimizer

class CustomOptimizer(SensorNetworkOptimizer):
    def optimize(self):
        # 实现你的优化算法
        pass
```

### 添加新的传感器类型
```python
# 扩展传感器类
from advanced_sensor_optimization import GroundSensor

class CustomSensor(GroundSensor):
    def __init__(self, id, x, y, special_param):
        super().__init__(id, x, y, radius=1.0)
        self.special_param = special_param
    
    def custom_coverage_calculation(self):
        # 自定义覆盖计算方法
        pass
```

### 集成新的约束条件
```python
# 扩展约束类
from advanced_sensor_optimization import ResourceConstraints

constraints = ResourceConstraints(
    max_satellites=5,
    max_ground_sensors=10,
    max_total_cost=1000,
    custom_constraint=custom_value  # 添加自定义约束
)
```

---

## 📚 详细文档

每个模块都包含详细的类和函数文档，使用Python的`help()`函数查看：

```python
import mclp_observation_station
help(mclp_observation_station.MCLPObservationStationSolver)

import advanced_sensor_optimization  
help(advanced_sensor_optimization.GeneticAlgorithmOptimizer)
```

---

## ⚡ 快速测试命令

```bash
# 测试所有基础功能
python -c "
from mclp_examples import main as test_mclp
from optimization_demo import main as test_opt
from advanced_optimization_demo import main as test_advanced

test_mclp()      # 测试MCLP基础功能
test_opt()       # 测试优化演示
test_advanced()  # 测试高级算法
"

# 批量性能测试
python advanced_optimization_demo.py test
```

---

## 🔍 故障排除

### 常见问题

1. **导入错误**: 确保所有依赖包已安装
2. **内存不足**: 调大`grid_resolution`参数，减小网格密度
3. **计算时间过长**: 减少`generations`或`max_iterations`参数
4. **覆盖率过低**: 增加传感器候选数量或调整约束条件

### 调试技巧

```python
# 启用详细输出
import logging
logging.basicConfig(level=logging.DEBUG)

# 调整算法参数
solver = MCLPObservationStationSolver(
    target_area_coords=area_coords,
    coverage_ratio=0.8,
    sensor_radius=3.0,
    grid_resolution=1.0  # 增大以提高速度
)
```

---

## 📧 技术支持

如有问题或建议，请查看各模块的文档字符串或运行内置的演示函数。每个主要模块都包含完整的示例代码和使用说明。

**开始探索**: 建议从 `mclp_observation_station.py` 开始，然后根据需求选择相应的高级功能模块！