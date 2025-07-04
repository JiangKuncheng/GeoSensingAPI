from skyfield.api import EarthSatellite, load
import numpy as np

def get_orbit_radius(tle_inputs: dict) -> dict:
    """
    计算多个卫星TLE字典中各卫星当前轨道半径（单位：千米）。

    参数:
        tle_inputs (dict): 字典形式，键为卫星名称，值为对应的TLE字符串（三行文本）

    返回:
        dict: 字典形式，键为卫星名称，值为轨道半径（单位：千米）。
              若TLE无效则对应值为 None。
    """
    ts = load.timescale()

    def calculate_radius(tle_data: str) -> float | None:
        lines = tle_data.strip().split("\n")
        if len(lines) < 3:
            return None

        try:
            satellite = EarthSatellite(lines[1], lines[2], lines[0], ts)
            t = ts.now()
            geocentric = satellite.at(t)
            position_km = float(np.linalg.norm(np.array(geocentric.position.km)))
            return position_km
        except Exception:
            return None

    if not isinstance(tle_inputs, dict):
        raise TypeError("输入应为字典，格式为 {卫星名: TLE字符串}")

    results = {}
    for name, tle_str in tle_inputs.items():
        results[name] = calculate_radius(tle_str)

    return results
