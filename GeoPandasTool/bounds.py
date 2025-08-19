import geopandas as gpd
import json
import os
from typing import Union, List, Dict
from shapely.geometry import shape, box

def bounds(geojson_names: Union[str, List[str]]) -> Union[str, Dict[str, str]]:
    """
    计算一个或多个 GeoJSON 文件的边界包围盒并保存为文件

    参数:
        geojson_names (Union[str, List[str]]):
            - 单个 GeoJSON 文件名（不含路径和扩展名）
            - 或多个文件名组成的列表

    返回:
        Union[str, Dict[str, str]]:
            - 如果传入单个名称，返回对应的输出文件名
            - 如果传入多个名称，返回字典，键为输入文件名，值为对应输出文件名
    """
    # 如果是单个字符串，转为列表处理
    is_single = isinstance(geojson_names, str)
    names = [geojson_names] if is_single else geojson_names
    results = {}
    
    for name in names:
        input_path = os.path.join("geojson", f"{name}.geojson")
        output_name = f"{name}_bounds"
        output_path = os.path.join("geojson", f"{output_name}.geojson")
        
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
            
            results[name] = output_name
            
        except Exception as e:
            results[name] = f"Error: {str(e)}"
    
    return results[geojson_names] if is_single else results


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
