from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Union, Dict

from GeoPandasTool.area import area
from satelliteTool.getPlaceBoundary import get_boundary
from satelliteTool.get_TLE_data import get_tle
from satelliteTool.get_orbit_radius import get_orbit_radius
from satelliteTool.get_orbit_velocity import calculate_velocity

app = FastAPI()


# === 获取TLE  ===
class TLERequest(BaseModel):
    satellite_names: Union[str, List[str]]


class TLEResponse(BaseModel):
    data: Dict[str, str]


@app.post("/get_tle", response_model=TLEResponse)
def fetch_tle(request: TLERequest):
    """
    通过卫星名称获取 TLE 数据。
    支持单个名称（字符串）或多个名称（列表）。
    """
    tle_data = get_tle(request.satellite_names)
    return {"data": tle_data}


# === 获取 GeoJSON 边界 ===
class BoundaryRequest(BaseModel):
    place_names: Union[str, List[str]]


class BoundaryResponse(BaseModel):
    data: Dict[str, str]


@app.post("/get_boundary", response_model=BoundaryResponse)
def fetch_boundary(request: BoundaryRequest):
    """
    通过地名获取行政边界 GeoJSON 文件路径。
    支持单个名称（字符串）或多个名称（列表）。
    """
    boundary_data = get_boundary(request.place_names)
    return {"data": boundary_data}


class AreaRequest(BaseModel):
    geojson_paths: Union[str, List[str]]

class AreaResponse(BaseModel):
    areas: Dict[str, List[float]]

@app.post("/area", response_model=AreaResponse)
def calculate_area(req: AreaRequest):
    try:
        result = area(req.geojson_paths)
        return {"areas": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))




class VelocityRequest(BaseModel):
    tle_dict: Dict[str, str]

# 返回体，字典形式：{name: velocity}
class VelocityResponse(BaseModel):
    velocities: Dict[str, float]

@app.post("/calculate_velocity", response_model=VelocityResponse)
def velocity_api(req: VelocityRequest):
    try:
        result = calculate_velocity(req.tle_dict)
        # 过滤掉解析失败的None，抛出异常或者改为0，根据需要调整
        if any(v is None for v in result.values()):
            raise ValueError("部分 TLE 数据无效或解析失败。")
        return {"velocities": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 定义请求体和响应体
class OrbitRadiusRequest(BaseModel):
    tle_dict: Dict[str, str]

class OrbitRadiusResponse(BaseModel):
    orbit_radii: Dict[str, float]


# 注册接口
@app.post("/calculate_orbit_radius", response_model=OrbitRadiusResponse)
def orbit_radius_api(req: OrbitRadiusRequest):
    try:
        result = get_orbit_radius(req.tle_dict)
        # 判断是否有None，视需求决定是否抛错
        if any(v is None for v in result.values()):
            raise ValueError("部分 TLE 数据无效或解析失败。")
        return {"orbit_radii": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


