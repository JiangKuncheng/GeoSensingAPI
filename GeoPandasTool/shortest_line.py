import geopandas as gpd
import json
import os
from typing import Union, List, Dict
from shapely.geometry import shape, mapping

def shortest_line_between_two(geojson_name1: str, geojson_name2: str) -> str:
    """
    计算两个 GeoJSON 文件中的地理对象之间的最短连接线并保存为文件

    参数:
        geojson_name1 (str): 第一个 GeoJSON 文件名（不含路径和扩展名）
        geojson_name2 (str): 第二个 GeoJSON 文件名（不含路径和扩展名）

    返回:
        str: 输出文件名
    """
    input_path1 = os.path.join("geojson", f"{geojson_name1}.geojson")
    input_path2 = os.path.join("geojson", f"{geojson_name2}.geojson")
    output_name = f"{geojson_name1}_{geojson_name2}_shortest_line"
    output_path = os.path.join("geojson", f"{output_name}.geojson")
    
    try:
        # 解析 GeoJSON 并提取第一个 geometry
        with open(input_path1, "r", encoding="utf-8") as f:
            geojson_data1 = json.load(f)
        with open(input_path2, "r", encoding="utf-8") as f:
            geojson_data2 = json.load(f)
        
        # 确保有features
        if not geojson_data1.get("features") or not geojson_data2.get("features"):
            raise ValueError("GeoJSON 必须包含 features")
        
        # 使用第一个feature进行计算
        geom1 = shape(geojson_data1["features"][0]["geometry"])
        geom2 = shape(geojson_data2["features"][0]["geometry"])

        # 构建 GeoSeries
        g1 = gpd.GeoSeries([geom1])
        g2 = gpd.GeoSeries([geom2])

        # 计算最短连接线
        shortest_line = g1.shortest_line(g2)[0]

        # 构造 GeoJSON Feature
        feature = {
            "type": "Feature",
            "geometry": json.loads(gpd.GeoSeries([shortest_line]).to_json())["features"][0]["geometry"],
            "properties": {}
        }

        # 构造 FeatureCollection
        result_geojson = {
            "type": "FeatureCollection",
            "features": [feature]
        }

        # 保存到文件
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_geojson, f, ensure_ascii=False, indent=2)
        
        return output_name
        
    except Exception as e:
        return f"Error: {str(e)}"

