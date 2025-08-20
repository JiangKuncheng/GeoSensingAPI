import geopandas as gpd
import json
import os
from typing import Union, List, Dict
from shapely.geometry import shape
from shapely.geometry import mapping

def clip_by_rect(geojson_names: Union[str, List[str]], xmin: float, ymin: float, xmax: float, ymax: float) -> Union[str, Dict[str, str]]:
    """
    裁剪一个或多个 GeoJSON 文件，使其仅保留指定矩形区域内的部分，并保存为文件

    参数:
        geojson_names (Union[str, List[str]]):
            - 单个 GeoJSON 文件名（不含路径和扩展名）
            - 或多个文件名组成的列表
        xmin (float): 矩形裁剪框的最小 x 坐标（左边界）
        ymin (float): 矩形裁剪框的最小 y 坐标（下边界）
        xmax (float): 矩形裁剪框的最大 x 坐标（右边界）
        ymax (float): 矩形裁剪框的最大 y 坐标（上边界）

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
        output_name = f"{name}_clipped"
        output_path = os.path.join("geojson", f"{output_name}.geojson")
        
        try:
            # 读取输入GeoJSON文件
            with open(input_path, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)

            # 提取几何对象
            geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]]

            # 构建 GeoSeries 并进行裁剪
            gseries = gpd.GeoSeries(geometries)
            clipped_gseries = gseries.clip_by_rect(xmin, ymin, xmax, ymax)

            # 生成新的 GeoJSON 结果
            clipped_features = []
            for i, geom in enumerate(clipped_gseries):
                if not geom.is_empty:  # 仅保留裁剪后仍有数据的对象
                    clipped_features.append({
                        "type": "Feature",
                        "geometry": mapping(geom),
                        "properties": geojson_data["features"][i].get("properties", {})  # 保留原始属性
                    })

            clipped_geojson = {
                "type": "FeatureCollection",
                "features": clipped_features
            }

            # 保存到文件
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(clipped_geojson, f, ensure_ascii=False, indent=2)
            
            results[name] = output_name
            
        except Exception as e:
            results[name] = f"Error: {str(e)}"

    return results[geojson_names] if is_single else results
