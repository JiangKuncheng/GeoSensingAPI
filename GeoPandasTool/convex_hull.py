import geopandas as gpd
import json
import os
from typing import Union, List, Dict
from shapely.geometry import shape
from shapely.geometry import mapping

def convex_hull(geojson_names: Union[str, List[str]]) -> Union[str, Dict[str, str]]:
    """
    计算一个或多个 GeoJSON 文件的凸包并保存为文件

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
        output_name = f"{name}_convex_hull"
        output_path = os.path.join("geojson", f"{output_name}.geojson")
        
        try:
            # 读取输入GeoJSON文件
            with open(input_path, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)

            # 提取几何对象
            geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]]

            # 构建 GeoSeries
            gseries = gpd.GeoSeries(geometries)

            # 计算凸包
            convex_hull_gseries = gseries.unary_union.convex_hull

            # 生成新的 GeoJSON 结果
            convex_hull_features = []
            if not convex_hull_gseries.is_empty:  # 仅保留非空对象
                convex_hull_features.append({
                    "type": "Feature",
                    "geometry": mapping(convex_hull_gseries),
                    "properties": {}  # 可根据需要添加属性
                })

            convex_hull_geojson = {
                "type": "FeatureCollection",
                "features": convex_hull_features
            }

            # 保存到文件
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(convex_hull_geojson, f, ensure_ascii=False, indent=2)
            
            results[name] = output_name
            
        except Exception as e:
            results[name] = f"Error: {str(e)}"

    return results[geojson_names] if is_single else results
