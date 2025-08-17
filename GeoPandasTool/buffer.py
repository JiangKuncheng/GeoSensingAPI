import geopandas as gpd
import json
import os
from shapely.geometry import shape

def buffer(multiInvocation=False, times=1, *args):
    """
    计算 GeoJSON 文件的缓冲区（buffer），支持多调用模式。

    单次调用:
        buffer(False, 1, input_path, distance, output_path)
    
    多次调用:
        buffer(True, 2, input_path1, distance1, output_path1, input_path2, distance2, output_path2)

    参数:
        multiInvocation (bool): 是否进行多次调用
        times (int): 调用次数（当 multiInvocation 为 True 时生效）
        args: 变长参数，每组参数包括 (input_path, distance, output_path)

    返回:
        list: 每次调用的结果状态
    """
    # 确保data目录存在
    os.makedirs("data", exist_ok=True)
    
    if multiInvocation:
        if len(args) != times * 3:
            raise ValueError(f"多次调用时参数数量应为 {times * 3}，实际为 {len(args)}")
        param_sets = [args[i:i + 3] for i in range(0, len(args), 3)]
    else:
        if len(args) != 3:
            raise ValueError("单次调用时需要提供 3 个参数：input_path, distance, output_path")
        param_sets = [args]

    results = []
    
    for input_path, distance, output_path in param_sets:
        try:
            # 读取输入GeoJSON文件
            with open(input_path, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)

            # 提取几何对象
            geometries = []
            if geojson_data.get("type") == "FeatureCollection":
                for feature in geojson_data["features"]:
                    geom = shape(feature["geometry"])
                    geometries.append(geom)
            elif geojson_data.get("type") == "Feature":
                geom = shape(geojson_data["geometry"])
                geometries.append(geom)
            else:
                raise ValueError(f"不支持的GeoJSON类型: {geojson_data.get('type')}")

            # 构建 GeoSeries 并计算缓冲区
            gseries = gpd.GeoSeries(geometries, crs="EPSG:4326")
            
            # 如果distance单位是米，需要转换坐标系
            if distance > 100:  # 假设大于100的是米为单位
                gseries_projected = gseries.to_crs("EPSG:3857")  # 转为墨卡托投影
                buffer_gseries = gseries_projected.buffer(distance)
                buffer_gseries = buffer_gseries.to_crs("EPSG:4326")  # 转回经纬度
            else:
                buffer_gseries = gseries.buffer(distance)  # 度为单位

            # 生成新的 GeoJSON 结果
            buffer_features = []
            for i, geom in enumerate(buffer_gseries):
                if not geom.is_empty:
                    buffer_features.append({
                        "type": "Feature",
                        "geometry": json.loads(geom.to_json()),
                        "properties": {"buffer_index": i}
                    })

            buffer_geojson = {
                "type": "FeatureCollection",
                "features": buffer_features
            }

            # 保存到输出文件
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(buffer_geojson, f, ensure_ascii=False, indent=2)
            
            results.append(f"成功: {input_path} -> {output_path}")
            
        except Exception as e:
            results.append(f"错误: {input_path} - {str(e)}")
    
    return results
