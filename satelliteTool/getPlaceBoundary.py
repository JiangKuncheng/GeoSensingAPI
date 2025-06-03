import os
import requests
import osm2geojson
import json
from typing import List, Union, Dict

OVERPASS_URL = "http://overpass-api.de/api/interpreter"
SAVE_DIR = "./geojson"

# 确保保存目录存在
os.makedirs(SAVE_DIR, exist_ok=True)

def fetch_boundary_and_save(place_name: str) -> Union[str, Dict[str, str]]:
    """
    获取单个地名的边界并保存为 GeoJSON 文件，返回文件路径或错误信息。
    """
    query = f"""
    [out:xml][timeout:25];
    relation["name:en"="{place_name}"]["boundary"="administrative"];
    out body;
    >;
    out skel qt;
    """
    response = requests.get(OVERPASS_URL, params={'data': query})

    if response.status_code == 200:
        geojson_data = osm2geojson.xml2geojson(response.text)
        file_path = os.path.join(SAVE_DIR, f"{place_name.replace(' ', '_')}.geojson")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, ensure_ascii=False, indent=2)
        return file_path
    else:
        return f"Request for '{place_name}' failed, status code {response.status_code}"


def get_boundary(place_names: Union[str, List[str]]) -> Union[str, Dict[str, str]]:
    """
    获取一个或多个地名的行政边界，并返回本地保存路径。
    :param place_names: 地名字符串或字符串列表
    :return: 单个路径或 {place_name: 路径}
    """
    results = {}
    if isinstance(place_names, str):

        results[place_names] = fetch_boundary_and_save(place_names)
        return results
    elif isinstance(place_names, list):
        # results = {}
        for name in place_names:
            results[name] = fetch_boundary_and_save(name)
        return results
    else:
        return "Invalid input type: place_names must be a string or a list of strings"
