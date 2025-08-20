import geopandas as gpd
import json
import os
from typing import Union, List, Dict
from shapely.geometry import shape
from shapely.geometry import mapping

def scale(geojson_names: Union[str, List[str]], xfact: float = 1.0, yfact: float = 1.0, origin: str = "center") -> Union[str, Dict[str, str]]:
    """
    缩放一个或多个 GeoJSON 文件中的几何对象并保存为文件

    参数:
        geojson_names (Union[str, List[str]]):
            - 单个 GeoJSON 文件名（不含路径和扩展名）
            - 或多个文件名组成的列表
        xfact (float): x 方向的缩放因子（默认为 1.0）
        yfact (float): y 方向的缩放因子（默认为 1.0）
        origin (str/tuple): 缩放中心，可选：
            - "center"（默认）：最小包围矩形的中心
            - "centroid"：几何质心
            - (x, y) 坐标点

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
        output_name = f"{name}_scaled"
        output_path = os.path.join("geojson", f"{output_name}.geojson")
        
        try:
            # 读取输入GeoJSON文件
            with open(input_path, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)

            # 提取几何对象
            geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]]

            # 构建 GeoSeries
            gseries = gpd.GeoSeries(geometries)

            # 进行几何缩放
            scaled_geometries = gseries.scale(xfact=xfact, yfact=yfact, origin=origin)

            # 生成新的 GeoJSON 结果
            scaled_features = []
            for geom in scaled_geometries:
                if not geom.is_empty:  # 仅保留非空对象
                    scaled_features.append({
                        "type": "Feature",
                        "geometry": mapping(geom),
                        "properties": {}  # 可根据需要添加属性
                    })

            scaled_geojson = {
                "type": "FeatureCollection",
                "features": scaled_features
            }

            # 保存到文件
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(scaled_geojson, f, ensure_ascii=False, indent=2)
            
            results[name] = output_name
            
        except Exception as e:
            results[name] = f"Error: {str(e)}"

    return results[geojson_names] if is_single else results
