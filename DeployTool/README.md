# 地面观测站布设问题求解器 (MCLP)

这是一个基于最大覆盖位置问题(Maximum Coverage Location Problem, MCLP)的地面观测站布设优化解决方案。该系统能够根据目标区域、覆盖要求和观测站参数，自动计算出最优的观测站布设方案。

## 功能特性

- **智能布设算法**: 基于贪心算法的最优观测站选址
- **灵活区域支持**: 支持矩形、多边形等各种复杂区域形状
- **精确覆盖计算**: 基于网格离散化的高精度覆盖率计算
- **可视化展示**: 直观的图形化结果展示，包括区域、观测站位置和覆盖范围
- **详细统计**: 提供完整的覆盖统计信息和结果导出
- **参数敏感性分析**: 支持不同参数配置的效果分析

## 系统要求

### 必需依赖
```
numpy >= 1.21.0
matplotlib >= 3.5.0
shapely >= 2.0.0
geopandas >= 0.10.0
```

### 可选依赖
```
pandas >= 1.3.0 (用于数据处理)
scipy >= 1.7.0 (用于高级优化算法)
```

## 安装与设置

1. **环境准备**
```bash
# 确保Python 3.8+
python --version

# 安装依赖包
pip install numpy matplotlib shapely geopandas pandas
```

2. **文件下载**
```bash
# 下载主要文件
wget mclp_observation_station.py
wget mclp_examples.py
```

## 快速开始

### 基础使用示例

```python
from mclp_observation_station import MCLPObservationStationSolver

# 定义目标区域（矩形）
area_coords = [(0, 0), (0, 10), (10, 10), (10, 0)]

# 创建求解器
solver = MCLPObservationStationSolver(
    target_area_coords=area_coords,
    coverage_ratio=0.8,        # 80%覆盖率
    sensor_radius=3.0,         # 观测半径3单位
    grid_resolution=0.5        # 网格分辨率
)

# 求解
stations, num_stations, actual_coverage = solver.solve()

# 显示结果
print(f"需要观测站数量: {num_stations}")
print(f"实际覆盖率: {actual_coverage*100:.2f}%")

# 可视化
solver.visualize()

# 导出结果
solver.export_results("result.txt")
```

### 高级使用示例

```python
# 不规则多边形区域
irregular_area = [
    (0, 0), (3, 1), (6, 0), (8, 3), (7, 6), 
    (5, 8), (3, 7), (1, 8), (-1, 5), (0, 2)
]

solver = MCLPObservationStationSolver(
    target_area_coords=irregular_area,
    coverage_ratio=0.85,
    sensor_radius=2.5,
    grid_resolution=0.3
)

stations, num_stations, actual_coverage = solver.solve()
solver.visualize(show_grid=True)
```

## 核心算法

### 贪心算法流程

1. **区域离散化**: 将目标区域划分为均匀网格点
2. **候选位置生成**: 在区域内外生成候选观测站位置
3. **迭代选择**: 每次选择能覆盖最多未覆盖点的位置
4. **覆盖验证**: 计算并验证是否满足覆盖要求
5. **结果优化**: 输出最少观测站数量的布设方案

### 关键参数说明

- **`coverage_ratio`**: 目标覆盖比例 (0-1)
- **`sensor_radius`**: 观测站覆盖半径
- **`grid_resolution`**: 网格分辨率，影响计算精度和速度
- **`target_area_coords`**: 目标区域顶点坐标列表

## API 参考

### MCLPObservationStationSolver 类

#### 构造函数
```python
__init__(target_area_coords, coverage_ratio, sensor_radius, grid_resolution=0.5)
```

#### 主要方法

- **`solve()`**: 执行求解算法
  - 返回: `(观测站位置列表, 观测站数量, 实际覆盖率)`

- **`visualize(show_grid=False, save_path=None)`**: 可视化结果
  - `show_grid`: 是否显示网格点
  - `save_path`: 保存图片路径

- **`get_coverage_statistics()`**: 获取详细统计信息
  - 返回: 包含各种统计数据的字典

- **`export_results(filename)`**: 导出结果到文件

## 使用场景

### 1. 环境监测
- 空气质量监测站布设
- 水质监测网络规划
- 气象观测站部署

### 2. 安全监控
- 城市安防摄像头布设
- 边界监控系统规划
- 交通监控网络设计

### 3. 科学研究
- 生态环境观测网络
- 地质监测站部署
- 海洋观测浮标布设

## 示例集合

运行 `mclp_examples.py` 查看更多复杂场景示例：

```bash
python mclp_examples.py
```

包含的示例：
- 不规则多边形区域
- 海岸线监测区域
- 城市区域监测
- 参数敏感性分析
- 网格分辨率比较

## 性能优化建议

### 计算性能
- 对于大区域，适当增加 `grid_resolution` 值
- 复杂区域可分解为多个子区域分别计算
- 使用多进程并行处理大规模问题

### 精度平衡
- `grid_resolution = 0.1-0.5`: 高精度，适合小区域
- `grid_resolution = 0.5-1.0`: 平衡精度，适合中等区域  
- `grid_resolution = 1.0-2.0`: 快速计算，适合大区域

### 内存管理
- 大区域建议分块处理
- 定期清理不需要的中间结果
- 考虑使用数据流处理大数据集

## 算法限制与注意事项

1. **计算复杂度**: O(n×m)，其中n为网格点数，m为候选位置数
2. **内存需求**: 与网格密度和区域大小成正比
3. **局部最优**: 贪心算法可能得到局部最优解
4. **边界效应**: 观测站可能被放置在区域边界外

## 扩展功能

### 高级优化算法
可以替换贪心算法为：
- 遗传算法 (GA)
- 模拟退火 (SA)  
- 粒子群优化 (PSO)
- 线性规划求解

### 约束条件扩展
- 地形约束（高程、坡度）
- 成本约束（建设成本、维护成本）
- 可达性约束（交通便利性）
- 环境约束（保护区限制）

## 故障排除

### 常见问题

1. **ImportError**: 检查依赖包是否正确安装
2. **内存不足**: 减小网格分辨率或分块处理
3. **求解时间过长**: 增加网格分辨率或优化候选位置
4. **覆盖率不足**: 检查观测半径设置和区域形状

### 调试建议

```python
# 启用详细输出
solver.solve()  # 会自动打印详细进度

# 检查网格生成
print(f"网格点数量: {len(solver.grid_points)}")

# 验证区域形状
solver.visualize(show_grid=True)
```

## 贡献与支持

### 报告问题
请提供以下信息：
- Python版本和操作系统
- 完整的错误信息
- 最小重现示例代码
- 输入数据示例

### 功能建议
欢迎提出以下类型的改进建议：
- 新的优化算法
- 性能优化方案
- 可视化增强
- API设计改进

## 许可证

MIT License - 详见 LICENSE 文件

## 更新日志

### v1.0.0 (2024-12)
- 初始版本发布
- 基础贪心算法实现
- 可视化功能
- 示例集合

---

**作者**: AI Assistant  
**联系**: 通过GitHub Issues  
**文档更新**: 2024年12月