import geopandas as gpd
import json
import os
from shapely.geometry import shape, box

def bounds(multiInvocation=False, times=1, *args):
    """
    计算 GeoJSON 文件的边界包围盒，支持多调用模式，并保存为GeoJSON格式。

    单次调用:
        bounds(False, 1, input_path, output_path)
    
    多次调用:
        bounds(True, 2, input_path1, output_path1, input_path2, output_path2)

    参数:
        multiInvocation (bool): 是否进行多次调用
        times (int): 调用次数（当 multiInvocation 为 True 时生效）
        args: 变长参数，每组参数包括 (input_path, output_path)

    返回:
        list: 每次调用的结果状态
    """
    # 确保data目录存在
    os.makedirs("data", exist_ok=True)
    
    if multiInvocation:
        if len(args) != times * 2:
            raise ValueError(f"多次调用时参数数量应为 {times * 2}，实际为 {len(args)}")
        param_sets = [args[i:i + 2] for i in range(0, len(args), 2)]
    else:
        if len(args) != 2:
            raise ValueError("单次调用时需要提供 2 个参数：input_path, output_path")
        param_sets = [args]

    results = []
    
    for input_path, output_path in param_sets:
        try:
            # 读取输入GeoJSON文件
            with open(input_path, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)

            # 提取几何对象
            geometries = _extract_geometries(geojson_data)
            
            # 构建 GeoSeries 并计算bounds
            gseries = gpd.GeoSeries(geometries, crs="EPSG:4326")
            total_bounds = gseries.total_bounds  # [minx, miny, maxx, maxy]
            
            # 创建边界框几何对象
            bbox_geometry = box(total_bounds[0], total_bounds[1], total_bounds[2], total_bounds[3])
            
            # 生成边界框 GeoJSON
            bounds_geojson = {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": json.loads(bbox_geometry.to_json()),
                    "properties": {
                        "minx": total_bounds[0],
                        "miny": total_bounds[1], 
                        "maxx": total_bounds[2],
                        "maxy": total_bounds[3],
                        "width": total_bounds[2] - total_bounds[0],
                        "height": total_bounds[3] - total_bounds[1]
                    }
                }]
            }

            # 保存到输出文件
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(bounds_geojson, f, ensure_ascii=False, indent=2)
            
            results.append(f"成功: {input_path} -> {output_path}")
            
        except Exception as e:
            results.append(f"错误: {input_path} - {str(e)}")
    
    return results


def _extract_geometries(geojson):
    """提取GeoJSON中的几何对象"""
    geometries = []
    if geojson.get("type") == "FeatureCollection":
        for feature in geojson["features"]:
            geom = shape(feature["geometry"])
            geometries.append(geom)
    elif geojson.get("type") == "Feature":
        geom = shape(geojson["geometry"])
        geometries.append(geom)
    else:
        raise ValueError(f"不支持的GeoJSON类型: {geojson.get('type')}")

    if not geometries:
        raise ValueError("未找到几何对象")
    return geometries
