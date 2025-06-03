from skyfield.api import load, EarthSatellite
import numpy as np

# 初始化时间尺度
ts = load.timescale()

def calculate_velocity(tle_inputs):
    def parse_and_calculate(tle_str):
        lines = tle_str.strip().split("\n")
        if len(lines) < 3:
            return None
        try:
            sat = EarthSatellite(lines[1], lines[2], lines[0], ts)
            t = ts.now()
            geocentric = sat.at(t)
            velocity = np.linalg.norm(geocentric.velocity.km_per_s)
            return velocity
        except Exception:
            return None

    if isinstance(tle_inputs, str):
        lines = tle_inputs.strip().split("\n")
        name = lines[0] if lines else "Unnamed"
        return {name: parse_and_calculate(tle_inputs)}
    elif isinstance(tle_inputs, list):
        return {
            tle.strip().split("\n")[0]: parse_and_calculate(tle)
            for tle in tle_inputs
        }
    elif isinstance(tle_inputs, dict):
        return {
            name: parse_and_calculate(tle)
            for name, tle in tle_inputs.items()
        }
    else:
        raise TypeError("输入应为字符串、列表或字典。")

