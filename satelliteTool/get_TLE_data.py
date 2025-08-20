
import requests
from urllib.parse import urlencode
from typing import List, Union, Dict


def get_tle(satellite_names: Union[str, List[str]]) -> Union[str, Dict[str, str]]:
    """
    获取一个或多个卫星的 TLE（Two-Line Element set）数据。

    参数:
        satellite_names (Union[str, List[str]]):
            单个卫星名称（字符串），或多个卫星名称组成的列表。

    返回:
        Union[str, Dict[str, str]]:
            - 如果传入单个名称，返回对应的 TLE 数据字符串。
            - 如果传入多个名称，返回一个字典，键为卫星名称，值为对应的 TLE 数据或错误信息。
    """
    base_url = "https://celestrak.org/NORAD/elements/gp.php?"

    # 如果是单个字符串，转为列表处理
    is_single = isinstance(satellite_names, str)
    names = [satellite_names] if is_single else satellite_names

    results = {}
    for satellite_name in names:
        params = {"FORMAT": "tle", "NAME": satellite_name}
        url = base_url + urlencode(params)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                tle_data = response.text.strip()
                results[satellite_name] = tle_data if tle_data else "No TLE data found"
            else:
                results[satellite_name] = f"Error: HTTP {response.status_code}"
        except Exception as e:
            results[satellite_name] = f"Exception occurred: {e}"

    return results[satellite_names] if is_single else results


if __name__ == '__main__':
    # 示例用法
    satellite_name = "Hodoyoshi_1"  # 可以更换为任意卫星名称
    tle_data = get_tle(satellite_name)
    print(tle_data)
