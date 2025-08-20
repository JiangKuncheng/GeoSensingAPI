import geopandas as gpd
import json
import os
from typing import Union, List, Dict
from shapely.geometry import shape

def union(geojson_name1: str, geojson_name2: str) -> str:
    """
    计算两个 GeoJSON 文件的并集并保存为文件

    参数:
        geojson_name1 (str): 第一个 GeoJSON 文件名（不含路径和扩展名）
        geojson_name2 (str): 第二个 GeoJSON 文件名（不含路径和扩展名）

    返回:
        str: 输出文件名
    """
    input_path1 = os.path.join("geojson", f"{geojson_name1}.geojson")
    input_path2 = os.path.join("geojson", f"{geojson_name2}.geojson")
    output_name = f"{geojson_name1}_{geojson_name2}_union"
    output_path = os.path.join("geojson", f"{output_name}.geojson")
    
    try:
        # 解析 GeoJSON 数据
        with open(input_path1, "r", encoding="utf-8") as f:
            geojson_data1 = json.load(f)
        with open(input_path2, "r", encoding="utf-8") as f:
            geojson_data2 = json.load(f)

        # 提取几何对象
        geometries1 = [shape(feature["geometry"]) for feature in geojson_data1["features"]]
        geometries2 = [shape(feature["geometry"]) for feature in geojson_data2["features"]]

        # 构建 GeoSeries
        gseries1 = gpd.GeoSeries(geometries1)
        gseries2 = gpd.GeoSeries(geometries2)

        # 计算并集
        union_gseries = gseries1.union(gseries2)

        # 生成新的 GeoJSON 结果
        union_features = []
        for geom in union_gseries:
            if not geom.is_empty:  # 仅保留非空对象
                union_features.append({
                    "type": "Feature",
                    "geometry": json.loads(geom.to_json()),
                    "properties": {}  # 可根据需要添加属性
                })

        union_geojson = {
            "type": "FeatureCollection",
            "features": union_features
        }

        # 保存到文件
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(union_geojson, f, ensure_ascii=False, indent=2)
        
        return output_name
        
    except Exception as e:
        return f"Error: {str(e)}"
