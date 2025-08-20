# -*- coding: utf-8 -*-
"""
几何图形清理和修复工具
功能：检测、修复和清理GeoJSON中的无效几何图形
"""

import json
from typing import Dict, List, Union, Tuple


def clean_geometries(geojson_input: Union[str, Dict], 
                     repair_invalid: bool = True,
                     remove_empty: bool = True,
                     remove_duplicates: bool = True,
                     simplify_tolerance: float = 0.0) -> Dict:
    """
    清理和修复GeoJSON中的无效几何图形
    
    Args:
        geojson_input: 输入的GeoJSON数据（字符串或字典）
        repair_invalid: 是否尝试修复无效几何图形，默认为True
        remove_empty: 是否移除空的几何图形，默认为True
        remove_duplicates: 是否移除重复的几何图形，默认为True
        simplify_tolerance: 几何简化容差，0表示不简化，默认为0.0
    
    Returns:
        Dict: 清理后的GeoJSON数据
    """
    
    try:
        # 解析输入数据
        if isinstance(geojson_input, str):
            geojson_data = json.loads(geojson_input)
        elif isinstance(geojson_input, dict):
            geojson_data = geojson_input
        else:
            raise ValueError("输入必须是GeoJSON字符串或字典")
        
        # 验证GeoJSON结构
        if not isinstance(geojson_data, dict) or 'type' not in geojson_data:
            raise ValueError("无效的GeoJSON结构")
        
        if geojson_data['type'] != 'FeatureCollection':
            raise ValueError("目前只支持FeatureCollection类型的GeoJSON")
        
        if 'features' not in geojson_data:
            raise ValueError("GeoJSON缺少features字段")
        
        print("开始清理几何图形...")
        
        # 统计信息
        total_features = len(geojson_data['features'])
        valid_features = []
        removed_count = 0
        repaired_count = 0
        
        # 用于检测重复的几何图形
        seen_geometries = set()
        
        for i, feature in enumerate(geojson_data['features']):
            try:
                # 检查feature结构
                if not isinstance(feature, dict) or 'geometry' not in feature:
                    removed_count += 1
                    continue
                
                geometry = feature.get('geometry')
                if not geometry or 'type' not in geometry or 'coordinates' not in geometry:
                    removed_count += 1
                    continue
                
                # 检查坐标是否为空
                coordinates = geometry.get('coordinates')
                if not coordinates or (isinstance(coordinates, list) and len(coordinates) == 0):
                    if remove_empty:
                        removed_count += 1
                        continue
                
                # 尝试验证和修复几何图形
                try:
                    from shapely.geometry import shape
                    from shapely.validation import make_valid
                    
                    # 创建几何对象
                    geom = shape(geometry)
                    
                    # 检查是否为空
                    if geom.is_empty:
                        if remove_empty:
                            removed_count += 1
                            continue
                        else:
                            valid_features.append(feature)
                            continue
                    
                    # 检查几何有效性
                    if not geom.is_valid and repair_invalid:
                        try:
                            fixed_geom = make_valid(geom)
                            
                            if fixed_geom and not fixed_geom.is_empty:
                                # 更新修复后的几何图形
                                feature['geometry'] = fixed_geom.__geo_interface__
                                repaired_count += 1
                            else:
                                if remove_empty:
                                    removed_count += 1
                                    continue
                        except Exception:
                            if remove_empty:
                                removed_count += 1
                                continue
                    
                    # 几何简化
                    if simplify_tolerance > 0:
                        try:
                            simplified_geom = geom.simplify(simplify_tolerance)
                            if simplified_geom and not simplified_geom.is_empty:
                                feature['geometry'] = simplified_geom.__geo_interface__
                        except Exception:
                            pass
                    
                    # 检查重复
                    if remove_duplicates:
                        # 创建几何图形的字符串表示用于去重
                        geom_str = json.dumps(feature['geometry'], sort_keys=True)
                        if geom_str in seen_geometries:
                            removed_count += 1
                            continue
                        seen_geometries.add(geom_str)
                    
                    # 添加到有效特征列表
                    valid_features.append(feature)
                    
                except Exception:
                    removed_count += 1
                    continue
                    
            except Exception:
                removed_count += 1
                continue
        
        # 创建清理后的GeoJSON
        cleaned_geojson = {
            'type': 'FeatureCollection',
            'features': valid_features
        }
        
        # 输出统计信息
        print("=" * 50)
        print("几何图形清理完成")
        print("=" * 50)
        print(f"原始特征数量: {total_features}")
        print(f"清理后特征数量: {len(valid_features)}")
        print(f"移除的特征数量: {removed_count}")
        print(f"修复的特征数量: {repaired_count}")
        print(f"保留率: {len(valid_features)/total_features*100:.1f}%")
        print("=" * 50)
        
        return cleaned_geojson
        
    except Exception as e:
        print(f"清理几何图形时出现错误: {e}")
        raise


def validate_geojson(geojson_input: Union[str, Dict]) -> Tuple[bool, List[str]]:
    """
    验证GeoJSON的有效性
    
    Args:
        geojson_input: 输入的GeoJSON数据
    
    Returns:
        Tuple[bool, List[str]]: (是否有效, 错误信息列表)
    """
    errors = []
    
    try:
        # 解析输入
        if isinstance(geojson_input, str):
            geojson_data = json.loads(geojson_input)
        elif isinstance(geojson_input, dict):
            geojson_data = geojson_input
        else:
            errors.append("输入必须是GeoJSON字符串或字典")
            return False, errors
        
        # 检查基本结构
        if not isinstance(geojson_data, dict):
            errors.append("GeoJSON必须是字典格式")
            return False, errors
        
        if 'type' not in geojson_data:
            errors.append("缺少type字段")
            return False, errors
        
        if geojson_data['type'] != 'FeatureCollection':
            errors.append("目前只支持FeatureCollection类型")
            return False, errors
        
        if 'features' not in geojson_data:
            errors.append("缺少features字段")
            return False, errors
        
        if not isinstance(geojson_data['features'], list):
            errors.append("features必须是列表")
            return False, errors
        
        # 检查每个feature
        for i, feature in enumerate(geojson_data['features']):
            if not isinstance(feature, dict):
                errors.append(f"Feature {i} 必须是字典格式")
                continue
            
            if 'geometry' not in feature:
                errors.append(f"Feature {i} 缺少geometry字段")
                continue
            
            geometry = feature['geometry']
            if not isinstance(geometry, dict):
                errors.append(f"Feature {i} 的geometry必须是字典格式")
                continue
            
            if 'type' not in geometry:
                errors.append(f"Feature {i} 的geometry缺少type字段")
                continue
            
            if 'coordinates' not in geometry:
                errors.append(f"Feature {i} 的geometry缺少coordinates字段")
                continue
            
            # 尝试验证几何图形
            try:
                from shapely.geometry import shape
                geom = shape(geometry)
                
                if geom.is_empty:
                    errors.append(f"Feature {i} 的几何图形为空")
                
                if not geom.is_valid:
                    errors.append(f"Feature {i} 的几何图形无效")
                    
            except Exception as e:
                errors.append(f"Feature {i} 的几何图形解析失败: {e}")
        
        return len(errors) == 0, errors
        
    except Exception as e:
        errors.append(f"验证过程中出现错误: {e}")
        return False, errors


if __name__ == "__main__":
    # 测试示例
    test_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                },
                "properties": {"name": "valid_polygon"}
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [0, 0]]]  # 无效的多边形
                },
                "properties": {"name": "invalid_polygon"}
            }
        ]
    }
    
    print("测试几何图形清理工具...")
    
    # 验证
    is_valid, errors = validate_geojson(test_geojson)
    print(f"验证结果: {is_valid}")
    if errors:
        print("错误信息:")
        for error in errors:
            print(f"  - {error}")
    
    # 清理
    cleaned = clean_geometries(test_geojson, repair_invalid=True)
    print(f"\n清理完成，输出特征数量: {len(cleaned['features'])}")
    
    # 保存结果
    with open('cleaned_test_geojson.json', 'w') as f:
        json.dump(cleaned, f, indent=2)
    print("结果已保存到 cleaned_test_geojson.json")