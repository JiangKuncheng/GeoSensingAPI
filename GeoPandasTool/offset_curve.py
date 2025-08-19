import geopandas as gpd
import json
import os
from typing import Union, List, Dict
from shapely.geometry import shape


def offset_curve(geojson_names: Union[str, List[str]], distance: float, side: str = 'right', resolution: int = 16, join_style: int = 1, mitre_limit: float = 5.0) -> Union[List[str], Dict[str, List[str]]]:
    """
    为一个或多个 GeoJSON 文件中的 LineString/MultiLineString 几何体生成 offset curve

    参数:
        geojson_names (Union[str, List[str]]):
            - 单个 GeoJSON 文件名（不含路径和扩展名）
            - 或多个文件名组成的列表
        distance (float): 偏移距离
        side (str): 'left' 或 'right'，偏移的方向 默认right
        resolution (int): 圆弧分割精度 默认16
        join_style (int): 连接样式，1=round, 2=mitre, 3=bevel 默认1
        mitre_limit (float): miter 连接样式时的限制 默认5.0

    返回:
        Union[List[str], Dict[str, List[str]]]:
            - 如果传入单个名称，返回对应的 WKT 字符串列表
            - 如果传入多个名称，返回字典，键为输入文件名，值为对应 WKT 字符串列表
    """
    # 如果是单个字符串，转为列表处理
    is_single = isinstance(geojson_names, str)
    names = [geojson_names] if is_single else geojson_names
    results = {}

    for name in names:
        input_path = os.path.join("geojson", f"{name}.geojson")
        
        try:
            # 读取输入GeoJSON文件
            with open(input_path, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)

            # 提取所有 geometry
            geometries = []
            if geojson_data.get("type") == "FeatureCollection":
                for feature in geojson_data["features"]:
                    geom = shape(feature["geometry"])
                    geometries.append(geom)
            elif geojson_data.get("type") == "Feature":
                geom = shape(geojson_data["geometry"])
                geometries.append(geom)
            else:
                raise ValueError("输入的GeoJSON不包含Feature或FeatureCollection")

            if not geometries:
                raise ValueError("GeoJSON中未找到有效的geometry")

            # 构建 GeoSeries
            gseries = gpd.GeoSeries(geometries)

            # 只对 LineString 或 MultiLineString 有意义
            valid_types = ["LineString", "MultiLineString"]
            if not all(geom.geom_type in valid_types for geom in gseries):
                raise ValueError("offset_curve 只能用于 LineString 或 MultiLineString 类型")

            # 计算 offset curve
            result = gseries.offset_curve(distance=distance, side=side, resolution=resolution, join_style=join_style,
                                          mitre_limit=mitre_limit)

            results[name] = [geom.wkt for geom in result]
            
        except Exception as e:
            results[name] = f"Error: {str(e)}"

    return results[geojson_names] if is_single else results
