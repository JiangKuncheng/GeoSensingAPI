# 工具组合汇总 (Tool Combinations Summary)

## 总工具数量
- **58个工具** (来自合并后的元数据文件)

## 基本组合类型

### 1. 两工具组合 (2-Tool Chains)
**数量**: 约 **150+ 种有效组合**

常见组合模式：
- `get_tle` → `get_satellite_footprint`
- `get_boundary` → `area`
- `buffer` → `intersects`
- `is_valid` → `is_valid_reason`
- `intersection` → `area`
- `centroid` → `buffer`

### 2. 三工具组合 (3-Tool Chains)  
**数量**: 约 **300+ 种有效组合**

常见组合模式：
- `get_tle` → `get_satellite_footprint` → `intersects`
- `get_boundary` → `buffer` → `area`
- `get_tle` → `get_orbit_inclination` → `get_orbit_radius`
- `intersection` → `is_valid` → `area`
- `buffer` → `intersection` → `area`

### 3. 四工具组合 (4-Tool Chains)
**数量**: 约 **200+ 种有效组合**

常见组合模式：
- `get_boundary` → `buffer` → `intersection` → `area`
- `get_tle` → `get_satellite_footprint` → `intersects` → `area`
- `is_valid` → `is_valid_reason` → `simplify` → `area`
- `query_satellite` → `get_tle` → `get_satellite_footprint` → `intersects`

### 4. 五工具及以上组合 (5+ Tool Chains)
**数量**: 约 **100+ 种有效组合**

复杂规划链：
- `query_satellite` → `get_tle` → `get_boundary` → `get_observation_overlap` → `area`
- `get_boundary` → `buffer` → `intersection` → `is_valid` → `area`

## 按工具类别的组合统计

### 卫星操作工具 (9个工具)
- 内部组合: **36种** 2-工具组合
- 与地理工具组合: **360种+**

### 地理空间处理工具 (20个工具)  
- 内部组合: **190种** 2-工具组合
- 与其他类别组合: **400种+**

### 几何关系工具 (14个工具)
- 内部组合: **91种** 2-工具组合  
- 与处理工具组合: **280种+**

### 几何验证工具 (7个工具)
- 内部组合: **21种** 2-工具组合
- 与其他工具组合: **350种+**

## 总组合估算

- **2工具链**: ~150种
- **3工具链**: ~300种  
- **4工具链**: ~200种
- **5+工具链**: ~100种

**总计**: 约 **750+ 种有意义的工具组合**

## 最常用的10种组合

1. `get_boundary` → `area`
2. `get_tle` → `get_satellite_footprint` 
3. `buffer` → `intersects`
4. `intersection` → `area`
5. `get_boundary` → `buffer` → `area`
6. `is_valid` → `is_valid_reason`
7. `centroid` → `buffer`
8. `get_tle` → `get_orbit_inclination`
9. `union` → `area`
10. `get_satellite_footprint` → `intersects` → `area`

这些组合覆盖了大部分实际使用场景。
