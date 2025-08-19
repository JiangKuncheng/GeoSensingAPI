import geopandas as gpd
import json
import os
from typing import Union, List, Dict
from shapely.geometry import shape

def symmetric_difference(geojson_names: Union[str, List[str]], clip_geojson_name: str) -> Union[str, Dict[str, str]]:
    """
    计算一个或多个 GeoJSON 文件与另一个 GeoJSON 文件的对称差并保存为文件

    参数:
        geojson_names (Union[str, List[str]]):
            - 单个 GeoJSON 文件名（不含路径和扩展名）
            - 或多个文件名组成的列表
        clip_geojson_name (str): 用于计算对称差的 GeoJSON 文件名

    返回:
        Union[str, Dict[str, str]]:
            - 如果传入单个名称，返回对应的输出文件名
            - 如果传入多个名称，返回字典，键为输入文件名，值为对应输出文件名
    """
    # 如果是单个字符串，转为列表处理
    is_single = isinstance(geojson_names, str)
    names = [geojson_names] if is_single else geojson_names
    results = {}

    # 读取裁剪 GeoJSON 文件
    clip_path = os.path.join("geojson", f"{clip_geojson_name}.geojson")
    with open(clip_path, "r", encoding="utf-8") as f:
        clip_geojson_data = json.load(f)
    clip_geometries = [shape(feature["geometry"]) for feature in clip_geojson_data["features"]]

    for name in names:
        input_path = os.path.join("geojson", f"{name}.geojson")
        output_name = f"{name}_symmetric_difference"
        output_path = os.path.join("geojson", f"{output_name}.geojson")
        
        try:
            # 读取输入GeoJSON文件
            with open(input_path, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)

            # 提取几何对象
            geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]]

            # 构建 GeoSeries
            gseries = gpd.GeoSeries(geometries)
            clip_series = gpd.GeoSeries(clip_geometries)

            # 计算对称差（symmetric_difference）
            sym_diff_gseries = gseries.symmetric_difference(clip_series.unary_union)  # 计算非重叠部分

            # 生成新的 GeoJSON 结果
            sym_diff_features = []
            for i, geom in enumerate(sym_diff_gseries):
                if not geom.is_empty:  # 仅保留非空对象
                    sym_diff_features.append({
                        "type": "Feature",
                        "geometry": json.loads(geom.to_json()),
                        "properties": geojson_data["features"][i].get("properties", {})  # 保留原始属性
                    })

            sym_diff_geojson = {
                "type": "FeatureCollection",
                "features": sym_diff_features
            }

            # 保存到文件
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(sym_diff_geojson, f, ensure_ascii=False, indent=2)
            
            results[name] = output_name
            
        except Exception as e:
            results[name] = f"Error: {str(e)}"

    return results[geojson_names] if is_single else results
