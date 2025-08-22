# 武汉降雨观测任务工作流程 (修订版)

## 📋 第1阶段：任务需求分析

### 用户原始需求
"观测武汉最近七天降雨"

### 结构化需求
```json
{
  "监测目标": "降雨",
  "监测区域": "武汉市",
  "时间范围": "最近七天",
  "监测参数": ["降雨量", "降雨分布"]
}
```

---

## 🔍 第2阶段：发现阶段

### 2.1 获取武汉市边界并保存
```python
# 使用 satelliteTool/getPlaceBoundary.py
wuhan_boundary_geojson = getPlaceBoundary("武汉市")

# 保存到data目录
import json
import os
os.makedirs("data", exist_ok=True)
with open("data/wuhan_boundary.geojson", "w", encoding="utf-8") as f:
    json.dump(wuhan_boundary_geojson, f, ensure_ascii=False, indent=2)

wuhan_boundary_path = "data/wuhan_boundary.geojson"
```

### 2.2 扩展监测范围
```python
# 修改 GeoPandasTool/buffer.py 支持多调用和GeoJSON文件存储
# multiInvocation=True, times=1
# geojson_paths=["data/wuhan_boundary.geojson"], buffer_distances=[5000], output_paths=["data/wuhan_buffered.geojson"]
buffer_result = buffer(
    multiInvocation=True, 
    times=1,
    "data/wuhan_boundary.geojson", 5000, "data/wuhan_buffered.geojson"
)

monitoring_area_path = "data/wuhan_buffered.geojson"
```

### 2.3 计算监测区域特征
```python
# 修改 GeoPandasTool/area.py 支持多文件计算
area_results = area(["data/wuhan_buffered.geojson"])
monitoring_area_size = area_results["data/wuhan_buffered.geojson"]

# 修改 GeoPandasTool/centroid.py 支持多调用
centroid_result = centroid(
    multiInvocation=True,
    times=1,
    "data/wuhan_buffered.geojson", "data/wuhan_center.geojson"
)

# 修改 GeoPandasTool/bounds.py 支持多调用
bounds_result = bounds(
    multiInvocation=True,
    times=1, 
    "data/wuhan_buffered.geojson", "data/wuhan_bounds.geojson"
)
```

### 2.4 批量获取卫星TLE数据
```python
# 使用 satelliteTool/get_TLE_data.py 批量获取
weather_satellites = [
    "NOAA 19", "NOAA 20", 
    "TERRA", "AQUA",
    "GAOFEN-4",
    "GAOFEN-1", "GAOFEN-2", "GAOFEN-3"
]

satellite_tle_data = get_tle(weather_satellites)
available_satellites = {}

for sat_name, tle in satellite_tle_data.items():
    if "Error" not in tle and "No GP data found" not in tle:
        available_satellites[sat_name] = tle
        
print(f"可用卫星: {list(available_satellites.keys())}")
```

### 2.5 批量计算卫星星下点覆盖轨迹
```python
# 使用 satelliteTool/get_observation_lace.py 进行多调用
# 计算过去7天每颗卫星的覆盖轨迹
import datetime

end_time = datetime.datetime.now()
start_time = end_time - datetime.timedelta(days=7)

# 准备多调用参数
lace_params = []
satellite_names = []

for sat_name, tle_data in available_satellites.items():
    satellite_names.append(sat_name)
    lace_params.extend([
        tle_data,
        start_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
        end_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
        3600,  # 1小时间隔
        60     # 视场角60度
    ])

# 多调用获取所有卫星覆盖轨迹
coverage_geojson = get_coverage_lace(
    multiInvocation=True,
    times=len(available_satellites),
    *lace_params
)

# 保存覆盖轨迹数据
with open("data/satellite_coverage_tracks.geojson", "w", encoding="utf-8") as f:
    json.dump(coverage_geojson, f, ensure_ascii=False, indent=2)
```

### 2.6 分析卫星覆盖与武汉区域的重叠
```python
# 使用 GeoPandasTool/overlaps.py 计算重叠
# 读取覆盖轨迹和武汉区域
with open("data/satellite_coverage_tracks.geojson", "r", encoding="utf-8") as f:
    coverage_data = json.load(f)

with open("data/wuhan_buffered.geojson", "r", encoding="utf-8") as f:
    wuhan_data = json.load(f)

# 计算重叠
overlap_results = overlaps(
    json.dumps(coverage_data), 
    json.dumps(wuhan_data)
)

print(f"覆盖重叠分析: {sum(overlap_results)}个轨迹与武汉有重叠")
```

### 2.7 判断卫星轨迹与武汉区域的交集
```python
# 使用 satelliteTool/has_intersection.py 判断交集
intersection_result = has_intersection(
    json.dumps(coverage_data),
    json.dumps(wuhan_data)
)

print(f"交集判断结果: {intersection_result}")

if intersection_result == "True":
    print("✅ 发现阶段完成：找到与武汉区域有交集的卫星观测数据")
else:
    print("❌ 未找到与武汉区域有交集的卫星观测数据")
```

### 2.8 统计每颗卫星的有效观测次数
```python
# 按卫星分组分析覆盖情况
satellite_coverage_stats = {}

for i, feature in enumerate(coverage_data['features']):
    satellite_name = feature['properties']['satellite']
    
    if satellite_name not in satellite_coverage_stats:
        satellite_coverage_stats[satellite_name] = {
            'total_observations': 0,
            'wuhan_overlaps': 0
        }
    
    satellite_coverage_stats[satellite_name]['total_observations'] += 1
    
    if overlap_results[i]:  # 如果这个观测与武汉有重叠
        satellite_coverage_stats[satellite_name]['wuhan_overlaps'] += 1

# 输出统计结果
print("\n📊 各卫星观测统计:")
for sat_name, stats in satellite_coverage_stats.items():
    coverage_ratio = stats['wuhan_overlaps'] / stats['total_observations']
    print(f"{sat_name}: {stats['wuhan_overlaps']}/{stats['total_observations']} ({coverage_ratio:.1%})")
```

---

## ⚙️ 第3阶段：配置阶段

### 说明
配置阶段代码在同门那里，暂时不实现。

---

## 📊 需要修改的工具

### 1. GeoPandasTool/buffer.py
```python
def buffer(multiInvocation=False, times=1, *args):
    """
    多调用版本：buffer(multiInvocation=True, times=2, 
                     "path1.geojson", distance1, "output1.geojson",
                     "path2.geojson", distance2, "output2.geojson")
    """
    # 实现多调用逻辑，结果保存到指定路径
```

### 2. GeoPandasTool/centroid.py
```python
def centroid(multiInvocation=False, times=1, *args):
    """
    多调用版本：centroid(multiInvocation=True, times=2,
                        "input1.geojson", "output1.geojson", 
                        "input2.geojson", "output2.geojson")
    """
    # 实现多调用逻辑，结果保存到data/目录
```

### 3. GeoPandasTool/bounds.py  
```python
def bounds(multiInvocation=False, times=1, *args):
    """
    多调用版本：bounds(multiInvocation=True, times=1,
                      "input.geojson", "output.geojson")
    """
    # 实现多调用逻辑，结果保存到data/目录
```

### 4. 数据存储结构
```
data/
├── wuhan_boundary.geojson          # 武汉边界
├── wuhan_buffered.geojson          # 缓冲区域  
├── wuhan_center.geojson            # 区域中心点
├── wuhan_bounds.geojson            # 边界框
└── satellite_coverage_tracks.geojson  # 卫星覆盖轨迹
```

---

## 🎯 工作流程特点

1. **GeoJSON本地存储**: 所有中间结果存储在data/目录
2. **批量处理**: TLE获取、星下点计算支持多卫星批量处理  
3. **覆盖分析**: 使用overlaps和has_intersection进行覆盖判断
4. **多调用支持**: 关键工具支持multiInvocation模式
5. **数据可追溯**: 每个处理步骤都有对应的GeoJSON文件保存
