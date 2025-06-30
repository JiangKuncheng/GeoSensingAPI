import json

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
from typing import List, Union, Dict, Optional, Tuple, Literal
import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import shape,mapping

from GeoPandasTool.area import area
from GeoPandasTool.boundary import boundary
from GeoPandasTool.bounds import bounds
from GeoPandasTool.buffer import buffer
from GeoPandasTool.centroid import centroid
from GeoPandasTool.clip_by_rect import clip_by_rect
from GeoPandasTool.concave_hull import concave_hull
from GeoPandasTool.contains import contains
from GeoPandasTool.contains_properly import contains_properly
from GeoPandasTool.convex_hull import convex_hull
from GeoPandasTool.covered_by import covered_by
from GeoPandasTool.covers import covers
from GeoPandasTool.crosses import crosses
from GeoPandasTool.difference import difference
from GeoPandasTool.disjoint import disjoint
from GeoPandasTool.distance import distance
from GeoPandasTool.dwithin import dwithin
from GeoPandasTool.envelope import envelope
from GeoPandasTool.exterior import exterior
from GeoPandasTool.geom_almost_equal import geom_almost_equal
from GeoPandasTool.geom_equals import geom_equals
from GeoPandasTool.geom_equals_exact import geom_equals_exact
from GeoPandasTool.intersection import intersection
from GeoPandasTool.intersects import intersects
from GeoPandasTool.is_ccw import is_ccw
from GeoPandasTool.is_closed import is_closed
from GeoPandasTool.is_empty import is_empty
from GeoPandasTool.is_ring import is_ring
from GeoPandasTool.is_simple import is_simple
from GeoPandasTool.is_valid import is_valid
from GeoPandasTool.is_valid_reason import is_valid_reason
from GeoPandasTool.length import length
from GeoPandasTool.line_merge import line_merge
from GeoPandasTool.minimum_bounding_radius import minimum_bounding_radius
from GeoPandasTool.offset_curve import offset_curve
from GeoPandasTool.overlaps import overlaps
from GeoPandasTool.remove_repeated_points import remove_repeated_points
from GeoPandasTool.reverse import reverse
from GeoPandasTool.rotate import rotate
from GeoPandasTool.scale import scale
from GeoPandasTool.shortest_line import shortest_line_between_two
from GeoPandasTool.simplify import simplify
from GeoPandasTool.symmetric_difference import symmetric_difference
from GeoPandasTool.total_bounds import total_bounds
from GeoPandasTool.touches import touches
from GeoPandasTool.translate import translate
from GeoPandasTool.union import union
from GeoPandasTool.within import within
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


class AreaRequest(BaseModel):
    paths: List[str]

@app.post("/area")
def compute_area(req: AreaRequest):
    """
    接收一个或多个本地 GeoJSON 文件路径，计算其中 Polygon / MultiPolygon 的总面积（平方米）
    """
    try:
        result = area(req.paths)
        return {
            "code": 0,
            "data": result,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class BoundaryRequest(BaseModel):
    geojson_list: List[str]            # 一个或多个 GeoJSON 字符串
    multiInvocation: bool = False      # 是否多输入处理
    times: int = 1                     # 多输入模式下的数量校验

@app.post("/boundary")
def compute_boundary(req: BoundaryRequest):
    """
    计算一个或多个 GeoJSON 字符串的边界线集合（boundary）
    """
    try:
        result = boundary(*req.geojson_list, multiInvocation=req.multiInvocation, times=req.times)

        # 结果为 GeoSeries 或 List[GeoSeries]，统一转为 GeoJSON
        if req.multiInvocation:
            result_geojson = []
            for gseries in result:
                fc = gpd.GeoSeries(gseries).to_json()
                result_geojson.append(json.loads(fc))
        else:
            result_geojson = json.loads(gpd.GeoSeries(result).to_json())

        return {
            "code": 0,
            "data": result_geojson,
            "message": "success"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class BoundsRequest(BaseModel):
    geojson_list: List[str]            # 一个或多个 GeoJSON 字符串
    multiInvocation: bool = False      # 是否处理多个输入
    times: int = 1                     # 如果启用 multiInvocation，必须匹配 geojson 数量

@app.post("/bounds")
def compute_bounds(req: BoundsRequest):
    """
    计算一个或多个 GeoJSON 的边界包围盒坐标（minx, miny, maxx, maxy）
    """
    try:
        result = bounds(*req.geojson_list, multiInvocation=req.multiInvocation, times=req.times)

        # pandas.DataFrame 或 List[pd.DataFrame] → dict 格式化
        if req.multiInvocation:
            serialized = [df.to_dict(orient="records") for df in result]
        else:
            serialized = result.to_dict(orient="records")

        return {
            "code": 0,
            "data": serialized,
            "message": "success"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class BufferRequest(BaseModel):
    geojson: str
    distance: float

@app.post("/buffer")
def compute_buffer(req: BufferRequest):
    """
    计算 GeoJSON 数据的缓冲区，并返回缓冲后的 GeoJSON 字符串
    """
    try:
        result = buffer(req.geojson, req.distance)
        return {
            "code": 0,
            "data": json.loads(result),  # 解析成对象结构，便于前端使用
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class CentroidRequest(BaseModel):
    geojson: str

@app.post("/centroid")
def compute_centroid(req: CentroidRequest):
    """
    计算 GeoJSON 中所有几何对象的质心（centroid）
    """
    try:
        result = centroid(req.geojson)
        return {
            "code": 0,
            "data": json.loads(result),  # 返回为 FeatureCollection 对象
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class ClipRequest(BaseModel):
    geojson: str
    xmin: float = Field(..., description="矩形裁剪框左边界")
    ymin: float = Field(..., description="矩形裁剪框下边界")
    xmax: float = Field(..., description="矩形裁剪框右边界")
    ymax: float = Field(..., description="矩形裁剪框上边界")

@app.post("/clip_by_rect")
def clip_geojson(req: ClipRequest):
    """
    裁剪 GeoJSON，使其只保留指定矩形区域内的部分
    """
    try:
        result = clip_by_rect(req.geojson, req.xmin, req.ymin, req.xmax, req.ymax)
        return {
            "code": 0,
            "data": json.loads(result),
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ConcaveHullRequest(BaseModel):
    geojson: str
    alpha: float = Field(0.05, description="影响凹壳形状的参数，越小越精细，越大越简洁")

@app.post("/concave_hull")
def compute_concave_hull(req: ConcaveHullRequest):
    """
    计算 GeoJSON 的凹壳（目前代码实际上为凸壳）
    """
    try:
        result = concave_hull(req.geojson, req.alpha)
        return {
            "code": 0,
            "data": json.loads(result),
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class ContainsRequest(BaseModel):
    geojson: str
    other_geojson: str

@app.post("/contains")
def check_contains(req: ContainsRequest):
    """
    判断 GeoJSON 中每个几何对象是否包含另一个 GeoJSON 中所有几何对象
    """
    try:
        result = contains(req.geojson, req.other_geojson)
        return {
            "code": 0,
            "data": result,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class ContainsProperlyRequest(BaseModel):
    geojson: str
    other_geojson: str

@app.post("/contains-properly")
def check_contains_properly(req: ContainsProperlyRequest):
    """
    判断 GeoJSON 中的每个 geometry 是否“正确地包含”另一个 GeoJSON 的所有 geometry
    """
    try:
        result = contains_properly(req.geojson, req.other_geojson)
        return {"code": 0, "data": result, "message": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ConvexHullRequest(BaseModel):
    geojson: str

@app.post("/convex-hull")
def compute_convex_hull(req: ConvexHullRequest):
    """
    计算输入 GeoJSON 的凸包，并返回 GeoJSON 格式的结果
    """
    try:
        result = convex_hull(req.geojson)
        return {
            "code": 0,
            "data": json.loads(result),  # 直接返回 JSON 对象，前端更易解析
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class CoveredByRequest(BaseModel):
    geojson: str
    container_geojson: str

@app.post("/covered-by")
def check_covered_by(req: CoveredByRequest):
    """
    判断 GeoJSON 中的每个 geometry 是否被另一个 GeoJSON 的 geometry 覆盖
    """
    try:
        result = covered_by(req.geojson, req.container_geojson)
        return {
            "code": 0,
            "data": result,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class CoversRequest(BaseModel):
    geojson: str
    other_geojson: str

@app.post("/covers")
def check_covers(req: CoversRequest):
    """
    判断 GeoJSON 中的每个 geometry 是否覆盖另一个 GeoJSON 中的任一 geometry
    """
    try:
        result = covers(req.geojson, req.other_geojson)
        return {
            "code": 0,
            "data": result,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class CrossesRequest(BaseModel):
    geojson: str
    other_geojson: str

@app.post("/crosses")
def check_crosses(req: CrossesRequest):
    """
    判断 GeoJSON 中的每个 geometry 是否与另一个 GeoJSON 中的任一 geometry 相交（crosses）
    """
    try:
        result = crosses(req.geojson, req.other_geojson)
        return {
            "code": 0,
            "data": result,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class DifferenceRequest(BaseModel):
    geojson: str
    clip_geojson: str

@app.post("/difference")
def compute_difference(req: DifferenceRequest):
    """
    计算两个 GeoJSON 的差集（difference）
    """
    try:
        result = difference(req.geojson, req.clip_geojson)
        return {
            "code": 0,
            "data": json.loads(result),
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class DisjointRequest(BaseModel):
    geojson: str
    other_geojson: str

@app.post("/disjoint")
def check_disjoint(req: DisjointRequest):
    """
    判断 GeoJSON 中每个几何对象是否与另一个 GeoJSON 中所有几何对象没有交集
    """
    try:
        result = disjoint(req.geojson, req.other_geojson)
        return {
            "code": 0,
            "data": result,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class DistanceRequest(BaseModel):
    geojson: str
    other_geojson: str

@app.post("/distance")
def compute_distance(req: DistanceRequest):
    """
    计算 GeoJSON 中每个几何对象到目标几何对象的距离
    """
    try:
        other_geojson = json.loads(req.other_geojson)

        # 提取目标 geometry（支持 FeatureCollection 或 Feature）
        other_geom = None
        if other_geojson.get("type") == "FeatureCollection":
            geoms = [shape(f["geometry"]) for f in other_geojson["features"]]
            # 目标几何合并为单一对象
            other_geom = unary_union(geoms)
        elif other_geojson.get("type") == "Feature":
            other_geom = shape(other_geojson["geometry"])
        else:
            raise ValueError("other_geojson 需包含 Feature 或 FeatureCollection")

        distances = distance(req.geojson, other_geom)

        return {
            "code": 0,
            "data": distances,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class DWithinRequest(BaseModel):
    geojson: str               # 主 GeoJSON 字符串
    other_geojson: str         # 目标 GeoJSON 字符串
    distance: float            # 距离阈值（单位取决于坐标系）

@app.post("/dwithin")
def dwithin_api(req: DWithinRequest):
    """
    判断主 GeoJSON 中的每个 geometry 是否与目标 GeoJSON 的任一 geometry 在指定距离内。
    """
    try:
        result = dwithin(req.geojson, req.other_geojson, req.distance)
        return {
            "code": 0,
            "data": result,  # 返回布尔值列表
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class EnvelopeRequest(BaseModel):
    geojson: str  # 输入 GeoJSON 字符串

@app.post("/envelope")
def envelope_api(req: EnvelopeRequest):
    """
    计算输入 GeoJSON 数据中每个 geometry 的外包络矩形。
    返回的是每个 geometry 的最小外接矩形构成的 FeatureCollection。
    """
    try:
        result = envelope(req.geojson)
        return {
            "code": 0,
            "data": result,  # 返回 GeoJSON 字符串
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class ExteriorRequest(BaseModel):
    geojson: str  # 输入的 GeoJSON 字符串

@app.post("/exterior")
def exterior_api(req: ExteriorRequest):
    """
    提取 GeoJSON 数据中 Polygon / MultiPolygon 几何的外边界（exterior）。

    返回:
        - 对 Polygon: LineString 对象
        - 对 MultiPolygon: LineString 列表
        - 其他类型: None
    """
    try:
        result = exterior(req.geojson)
        # shapely 对象需转为可序列化格式
        serialized = []
        for item in result:
            if item is None:
                serialized.append(None)
            elif isinstance(item, list):  # MultiPolygon 的多条外边界
                serialized.append([json.loads(geom.__geo_interface__.to_json()) for geom in item])
            else:  # Polygon 的单个外边界
                serialized.append(json.loads(item.__geo_interface__.to_json()))

        return {
            "code": 0,
            "data": serialized,
            "message": "success"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class GeomAlmostEqualRequest(BaseModel):
    geojson: str  # 主 GeoJSON 字符串
    other_geojson: str  # 目标 GeoJSON 字符串
    tolerance: Optional[float] = 1e-9  # 容差（可选）

@app.post("/geom_almost_equal")
def geom_almost_equal_api(req: GeomAlmostEqualRequest):
    """
    判断 GeoJSON 中的几何对象是否在容差范围内几乎相等。

    请求参数:
    - geojson: 主 GeoJSON 字符串
    - other_geojson: 对比的 GeoJSON 字符串
    - tolerance: 容差值（可选）

    返回:
    - 每个主 geometry 与目标集合是否 almost equal 的布尔值列表
    """
    try:
        result = geom_almost_equal(req.geojson, req.other_geojson, req.tolerance)
        return {
            "code": 0,
            "data": result,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class GeomEqualsRequest(BaseModel):
    geojson: str  # 主 GeoJSON 字符串
    other_geojson: str  # 目标 GeoJSON 字符串

@app.post("/geom_equals")
def geom_equals_api(req: GeomEqualsRequest):
    """
    判断主 GeoJSON 中每个 geometry 是否与目标 GeoJSON 中某 geometry 完全相同。

    请求体参数:
    - geojson: 主 GeoJSON 字符串
    - other_geojson: 目标 GeoJSON 字符串

    返回:
    - List[bool]: 布尔值列表，每个代表一个主 geometry 的判断结果
    """
    try:
        result = geom_equals(req.geojson, req.other_geojson)
        return {
            "code": 0,
            "data": result,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class GeomEqualsExactRequest(BaseModel):
    geojson: str  # 主 GeoJSON 字符串
    other_geojson: str  # 目标 GeoJSON 字符串
    tolerance: Optional[float] = 1e-9  # 容差，默认值为 1e-9

@app.post("/geom_equals_exact")
def geom_equals_exact_api(req: GeomEqualsExactRequest):
    """
    判断主 GeoJSON 中的几何对象是否与目标 GeoJSON 中的某些对象在容差范围内完全相同。

    请求体字段:
    - geojson: 主 GeoJSON 字符串
    - other_geojson: 对比用 GeoJSON 字符串
    - tolerance: 容差（默认 1e-9）

    返回值:
    - List[bool]: 每个 geometry 对象是否与另一组对象完全相等（带容差）
    """
    try:
        result = geom_equals_exact(req.geojson, req.other_geojson, req.tolerance)
        return {
            "code": 0,
            "data": result,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class IntersectionRequest(BaseModel):
    geojson: str  # 需要计算交集的 GeoJSON 字符串
    clip_geojson: str  # 用于计算交集的 GeoJSON 字符串

@app.post("/intersection")
def intersection_api(req: IntersectionRequest):
    """
    计算两个 GeoJSON 对象的交集。

    请求字段：
    - geojson: 主 GeoJSON 字符串
    - clip_geojson: 裁剪用 GeoJSON 字符串

    返回字段：
    - code: 状态码（0 表示成功）
    - data: 交集后的 GeoJSON 字符串
    - message: 返回信息
    """
    try:
        result = intersection(req.geojson, req.clip_geojson)
        return {
            "code": 0,
            "data": result,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class IntersectsRequest(BaseModel):
    geojson: str  # 主 GeoJSON 字符串
    other_geojson: str  # 目标 GeoJSON 字符串

@app.post("/intersects")
def intersects_api(req: IntersectsRequest):
    """
    判断主 GeoJSON 中的每个 geometry 是否与另一个 GeoJSON 中任意 geometry 相交。

    请求体字段：
    - geojson: 主 GeoJSON 字符串
    - other_geojson: 目标 GeoJSON 字符串

    返回值：
    - code: 状态码，0 表示成功
    - data: 每个 geometry 的布尔判断结果列表
    - message: 返回信息
    """
    try:
        result = intersects(req.geojson, req.other_geojson)
        return {
            "code": 0,
            "data": result,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class IsCCWRequest(BaseModel):
    geojson: str  # 输入的 GeoJSON 字符串

@app.post("/is_ccw")
def is_ccw_api(req: IsCCWRequest):
    """
    判断 GeoJSON 中每个几何对象的外环顶点是否为逆时针方向（CCW）。

    请求体:
    - geojson: GeoJSON 字符串

    返回:
    - code: 状态码，0 表示成功
    - data: 每个几何对象是否逆时针的布尔列表
    - message: 返回信息
    """
    try:
        result = is_ccw(req.geojson)
        return {
            "code": 0,
            "data": result,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class IsClosedRequest(BaseModel):
    geojson: str  # 输入的 GeoJSON 字符串

@app.post("/is_closed")
def is_closed_api(req: IsClosedRequest):
    """
    判断 GeoJSON 中每个几何对象是否闭合。

    请求体参数:
    - geojson: GeoJSON 字符串

    返回:
    - code: 状态码，0 表示成功
    - data: 每个 geometry 是否闭合的布尔列表
    - message: 返回信息
    """
    try:
        result = is_closed(req.geojson)
        return {
            "code": 0,
            "data": result,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class IsEmptyRequest(BaseModel):
    geojson: str  # 输入的 GeoJSON 字符串

@app.post("/is_empty")
def is_empty_api(req: IsEmptyRequest):
    """
    判断 GeoJSON 中每个几何对象是否为空。

    请求体参数:
    - geojson: GeoJSON 字符串

    返回:
    - code: 状态码，0 表示成功
    - data: 每个 geometry 是否为空的布尔列表
    - message: 返回信息
    """
    try:
        result = is_empty(req.geojson)
        return {
            "code": 0,
            "data": result,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class IsRingRequest(BaseModel):
    geojson: str  # 输入的 GeoJSON 字符串

@app.post("/is_ring")
def is_ring_api(req: IsRingRequest):
    """
    判断 GeoJSON 中每个 LineString 几何对象是否是 ring（闭合且简单）。

    请求体参数:
    - geojson: GeoJSON 字符串

    返回:
    - code: 状态码，0 表示成功
    - data: 每个 geometry 是否为 ring 的布尔列表
    - message: 返回信息
    """
    try:
        result = is_ring(req.geojson)
        return {
            "code": 0,
            "data": result,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class IsSimpleRequest(BaseModel):
    geojson: str  # 输入的 GeoJSON 字符串

@app.post("/is_simple")
def is_simple_api(req: IsSimpleRequest):
    """
    判断 GeoJSON 中每个几何对象是否为 simple（即不自交）

    请求参数:
    - geojson: GeoJSON 字符串

    返回:
    - code: 状态码，0 表示成功
    - data: 布尔列表，表示每个 geometry 是否为 simple
    - message: 返回信息
    """
    try:
        result = is_simple(req.geojson)
        return {
            "code": 0,
            "data": result,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class IsValidRequest(BaseModel):
    geojson: str  # 输入的 GeoJSON 字符串

@app.post("/is_valid")
def is_valid_api(req: IsValidRequest):
    """
    判断 GeoJSON 中每个几何对象是否是有效的合法几何。

    请求参数:
    - geojson: GeoJSON 字符串

    返回:
    - code: 状态码，0 表示成功
    - data: 布尔列表，表示每个 geometry 是否有效
    - message: 返回信息
    """
    try:
        result = is_valid(req.geojson)
        return {
            "code": 0,
            "data": result,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class IsValidReasonRequest(BaseModel):
    geojson: str  # 输入的 GeoJSON 字符串

@app.post("/is_valid_reason")
def is_valid_reason_api(req: IsValidReasonRequest):
    """
    返回每个几何对象合法性检查的原因说明。

    请求参数:
    - geojson: GeoJSON 字符串

    返回:
    - code: 状态码，0 表示成功
    - data: 字符串列表，每个元素为对应 geometry 的合法性检查说明
    - message: 返回信息
    """
    try:
        result = is_valid_reason(req.geojson)
        return {
            "code": 0,
            "data": result,
            "message": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class LengthRequest(BaseModel):
    geojson_str: str  # 输入的 GeoJSON 字符串

class LengthResponse(BaseModel):
    code: int
    data: List[float]
    message: str

@app.post("/length", response_model=LengthResponse)
def length_api(req: LengthRequest):
    """
    计算 Overpass API 导出的 GeoJSON 中每个 geometry 的长度。

    参数:
        geojson_str: GeoJSON 字符串

    返回:
        code: 状态码，0 表示成功
        data: 每个 geometry 的长度列表
        message: 结果描述
    """
    try:
        result = length(req.geojson_str)
        return LengthResponse(code=0, data=result, message="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class LineMergeRequest(BaseModel):
    geojson_str: str

class LineMergeResponse(BaseModel):
    code: int
    data: str
    message: str

@app.post("/line_merge", response_model=LineMergeResponse)
def line_merge_api(req: LineMergeRequest):
    """
    合并 Overpass API 获取的 GeoJSON 数据中的 LineString 线段。

    请求参数:
    - geojson_str: 输入的 GeoJSON 字符串

    返回:
    - code: 0 表示成功
    - data: 合并后的 GeoJSON 字符串（格式化）
    - message: 返回信息
    """
    try:
        merged_geojson_str = line_merge(req.geojson_str)
        merged_geojson = json.loads(merged_geojson_str)  # 转成 dict 方便返回
        return LineMergeResponse(code=0, data=merged_geojson, message="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class MBRRequest(BaseModel):
    geojson_str: str

class MBRResponse(BaseModel):
    code: int
    data: List[float]
    message: str

@app.post("/minimum_bounding_radius", response_model=MBRResponse)
def minimum_bounding_radius_api(req: MBRRequest):
    """
    计算 Overpass API 获取的 GeoJSON 中各 geometry 的最小外接圆半径。

    请求参数:
    - geojson_str: GeoJSON 字符串

    返回:
    - code: 状态码，0 表示成功
    - data: 各 geometry 的最小外接圆半径列表
    - message: 返回信息
    """
    try:
        result = minimum_bounding_radius(req.geojson_str)
        return MBRResponse(code=0, data=result, message="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class OffsetCurveRequest(BaseModel):
    geojson_str: str = Field(..., description="Overpass API 返回的 GeoJSON 字符串")
    distance: float = Field(..., description="偏移距离")
    side: Optional[Literal['left', 'right']] = Field('right', description="偏移方向，left 或 right，默认 right")
    resolution: Optional[int] = Field(16, description="圆弧分割精度，默认16")
    join_style: Optional[int] = Field(1, description="连接样式，1=round, 2=mitre, 3=bevel，默认1")
    mitre_limit: Optional[float] = Field(5.0, description="miter连接样式时的限制，默认5.0")

class OffsetCurveResponse(BaseModel):
    code: int
    data: List[str]  # WKT字符串列表
    message: str

@app.post("/offset_curve", response_model=OffsetCurveResponse)
def offset_curve_api(req: OffsetCurveRequest):
    """
    生成 LineString/MultiLineString 的 offset curve。

    请求参数:
    - geojson_str: GeoJSON 字符串
    - distance: 偏移距离
    - side: 偏移方向，left 或 right，默认 right
    - resolution: 圆弧分割精度，默认16
    - join_style: 连接样式，1=round, 2=mitre, 3=bevel，默认1
    - mitre_limit: miter连接限制，默认5.0

    返回:
    - code: 0 表示成功
    - data: 偏移后的 geometry 的 WKT 表达
    - message: 返回信息
    """
    try:
        result = offset_curve(
            req.geojson_str,
            req.distance,
            side=req.side,
            resolution=req.resolution,
            join_style=req.join_style,
            mitre_limit=req.mitre_limit
        )
        return OffsetCurveResponse(code=0, data=result, message="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class OverlapsRequest(BaseModel):
    geojson_str: str = Field(..., description="主 GeoJSON 字符串")
    other_geojson_str: str = Field(..., description="目标 GeoJSON 字符串")

class OverlapsResponse(BaseModel):
    code: int
    data: List[bool]
    message: str

@app.post("/overlaps", response_model=OverlapsResponse)
def overlaps_api(req: OverlapsRequest):
    """
    判断 GeoJSON 中的几何对象是否与目标几何对象部分重叠。

    请求参数:
    - geojson_str: 主 GeoJSON 字符串
    - other_geojson_str: 目标 GeoJSON 字符串

    返回:
    - code: 0 表示成功
    - data: 布尔列表，每个 geometry 是否部分重叠
    - message: 返回信息
    """
    try:
        result = overlaps(req.geojson_str, req.other_geojson_str)
        return OverlapsResponse(code=0, data=result, message="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class RemoveRepeatedPointsRequest(BaseModel):
    geojson_str: str = Field(..., description="输入的 GeoJSON 字符串")

class RemoveRepeatedPointsResponse(BaseModel):
    code: int
    data: str  # 去除重复点后的 GeoJSON 字符串
    message: str

@app.post("/remove_repeated_points", response_model=RemoveRepeatedPointsResponse)
def remove_repeated_points_api(req: RemoveRepeatedPointsRequest):
    """
    移除 Overpass API 获取的 GeoJSON 数据中的重复点。

    请求参数:
    - geojson_str: 输入的 GeoJSON 字符串

    返回:
    - code: 状态码，0 表示成功
    - data: 去除重复点后的 GeoJSON 字符串
    - message: 返回信息
    """
    try:
        result_geojson = remove_repeated_points(req.geojson_str)
        return RemoveRepeatedPointsResponse(code=0, data=result_geojson, message="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"处理失败: {str(e)}")

class ReverseRequest(BaseModel):
    geojson_str: str = Field(..., description="Overpass API 返回的 GeoJSON 字符串")

class ReverseResponse(BaseModel):
    code: int
    data: str  # 反转后的 GeoJSON 字符串
    message: str

@app.post("/reverse", response_model=ReverseResponse)
def reverse_api(req: ReverseRequest):
    """
    反转 Overpass API 获取的 GeoJSON 中几何对象的坐标顺序。

    请求参数:
    - geojson_str: GeoJSON 字符串

    返回:
    - code: 0 表示成功
    - data: 反转后的 GeoJSON 字符串
    - message: 返回信息
    """
    try:
        reversed_geojson = reverse(req.geojson_str)
        return ReverseResponse(code=0, data=reversed_geojson, message="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class RotateRequest(BaseModel):
    geojson_str: str = Field(..., description="Overpass API 返回的 GeoJSON 字符串")
    angle: float = Field(..., description="旋转角度（默认为度，use_radians=True 时为弧度）")
    origin: Union[str, Tuple[float, float]] = Field('centroid', description="旋转中心，可为 'centroid'、'center' 或指定坐标 (x, y)")
    use_radians: bool = Field(False, description="是否使用弧度进行旋转")

class RotateResponse(BaseModel):
    code: int
    data: str  # 旋转后的 GeoJSON 字符串
    message: str

@app.post("/rotate", response_model=RotateResponse)
def rotate_api(req: RotateRequest):
    """
    旋转 Overpass API 获取的 GeoJSON 中几何对象。

    请求参数:
    - geojson_str: GeoJSON 字符串
    - angle: 旋转角度
    - origin: 旋转中心
    - use_radians: 是否使用弧度

    返回:
    - code: 0 表示成功
    - data: 旋转后的 GeoJSON 字符串
    - message: 返回信息
    """
    try:
        rotated_geojson = rotate(req.geojson_str, req.angle, req.origin, req.use_radians)
        return RotateResponse(code=0, data=rotated_geojson, message="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class ScaleRequest(BaseModel):
    geojson_str: str = Field(..., description="Overpass API 返回的 GeoJSON 字符串")
    xfact: float = Field(1.0, description="x 方向的缩放因子")
    yfact: float = Field(1.0, description="y 方向的缩放因子")
    origin: Union[str, Tuple[float, float]] = Field("center", description="缩放中心，可为 'center', 'centroid', 或 (x, y) 坐标")

class ScaleResponse(BaseModel):
    code: int
    data: str  # 缩放后的 GeoJSON 字符串
    message: str

@app.post("/scale", response_model=ScaleResponse)
def scale_api(req: ScaleRequest):
    """
    缩放 Overpass API 获取的 GeoJSON 中几何对象。

    请求参数:
    - geojson_str: GeoJSON 字符串
    - xfact: x 方向缩放因子
    - yfact: y 方向缩放因子
    - origin: 缩放中心

    返回:
    - code: 0 表示成功
    - data: 缩放后的 GeoJSON 字符串
    - message: 返回信息
    """
    try:
        scaled_geojson = scale(req.geojson_str, req.xfact, req.yfact, req.origin)
        return ScaleResponse(code=0, data=scaled_geojson, message="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class ShortestLineRequest(BaseModel):
    geojson_str1: str = Field(..., description="第一个 GeoJSON 字符串，包含一个几何对象")
    geojson_str2: str = Field(..., description="第二个 GeoJSON 字符串，包含一个几何对象")

class ShortestLineResponse(BaseModel):
    code: int
    data: str  # 返回的最短连接线 GeoJSON 字符串
    message: str

@app.post("/shortest_line_between_two", response_model=ShortestLineResponse)
def shortest_line_api(req: ShortestLineRequest):
    """
    计算两个 GeoJSON 中地理对象之间的最短连接线

    请求参数:
    - geojson_str1: 第一个 GeoJSON 字符串
    - geojson_str2: 第二个 GeoJSON 字符串

    返回:
    - code: 0 表示成功
    - data: 最短连接线的 GeoJSON 字符串
    - message: 返回信息
    """
    try:
        result_geojson = shortest_line_between_two(req.geojson_str1, req.geojson_str2)
        # 确保结果是合法的 JSON 字符串
        json.loads(result_geojson)
        return ShortestLineResponse(code=0, data=result_geojson, message="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error computing shortest line: {str(e)}")

class SimplifyRequest(BaseModel):
    geojson_str: str = Field(..., description="Overpass API 返回的 GeoJSON 字符串")
    tolerance: Optional[float] = Field(0.01, description="简化程度，值越大简化越明显")
    preserve_topology: Optional[bool] = Field(True, description="是否保持拓扑结构")

class SimplifyResponse(BaseModel):
    code: int
    data: str  # 简化后的 GeoJSON 字符串
    message: str

@app.post("/simplify", response_model=SimplifyResponse)
def simplify_api(req: SimplifyRequest):
    """
    简化 Overpass API 获取的 GeoJSON 中几何对象。

    请求参数:
    - geojson_str: GeoJSON 字符串
    - tolerance: 简化容差
    - preserve_topology: 是否保持拓扑结构

    返回:
    - code: 0 表示成功
    - data: 简化后的 GeoJSON 字符串
    - message: 返回信息
    """
    try:
        result = simplify(req.geojson_str, req.tolerance, req.preserve_topology)
        return SimplifyResponse(code=0, data=result, message="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"简化失败: {str(e)}")

class SymmetricDifferenceRequest(BaseModel):
    geojson_str: str = Field(..., description="需要计算对称差的主 GeoJSON 字符串")
    clip_geojson_str: str = Field(..., description="用于计算对称差的 GeoJSON 字符串")

class SymmetricDifferenceResponse(BaseModel):
    code: int
    data: str  # 计算对称差后的 GeoJSON 字符串
    message: str

@app.post("/symmetric_difference", response_model=SymmetricDifferenceResponse)
def symmetric_difference_api(req: SymmetricDifferenceRequest):
    """
    计算 Overpass API 获取的 GeoJSON 数据与另一个几何对象的对称差 (symmetric_difference)。

    请求参数:
    - geojson_str: 主 GeoJSON 字符串
    - clip_geojson_str: 用于计算对称差的 GeoJSON 字符串

    返回:
    - code: 0 表示成功
    - data: 计算对称差后的 GeoJSON 字符串
    - message: 返回信息
    """
    try:
        result = symmetric_difference(req.geojson_str, req.clip_geojson_str)
        return SymmetricDifferenceResponse(code=0, data=result, message="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"对称差计算失败: {str(e)}")

class TotalBoundsRequest(BaseModel):
    geojson_str: str = Field(..., description="Overpass API返回的GeoJSON字符串")

class TotalBoundsResponse(BaseModel):
    code: int
    data: list[float]  # [minx, miny, maxx, maxy]
    message: str

@app.post("/total_bounds", response_model=TotalBoundsResponse)
def total_bounds_api(req: TotalBoundsRequest):
    """
    计算 Overpass API 导出的 GeoJSON 中所有 geometry 的整体包围盒

    请求参数:
    - geojson_str: GeoJSON 字符串

    返回:
    - code: 0 表示成功
    - data: [minx, miny, maxx, maxy]
    - message: 返回信息
    """
    try:
        bounds = total_bounds(req.geojson_str)
        return TotalBoundsResponse(code=0, data=bounds, message="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"计算包围盒失败: {str(e)}")

class TouchesRequest(BaseModel):
    geojson_str: str = Field(..., description="主 GeoJSON 字符串")
    other_geojson_str: str = Field(..., description="目标 GeoJSON 字符串，用于判断是否接触")

class TouchesResponse(BaseModel):
    code: int
    data: List[bool]
    message: str

@app.post("/touches", response_model=TouchesResponse)
def touches_api(req: TouchesRequest):
    """
    判断 Overpass API 获取的 GeoJSON 数据中的几何对象是否仅在边界上接触目标几何对象。

    请求参数:
    - geojson_str: 主 GeoJSON 字符串
    - other_geojson_str: 目标 GeoJSON 字符串

    返回:
    - code: 状态码，0表示成功
    - data: 每个 geometry 是否仅在边界上接触目标 geometry 的布尔列表
    - message: 返回信息
    """
    try:
        result = touches(req.geojson_str, req.other_geojson_str)
        return TouchesResponse(code=0, data=result, message="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"判断接触失败: {str(e)}")

class TranslateRequest(BaseModel):
    geojson_str: str = Field(..., description="Overpass API 返回的 GeoJSON 字符串")
    xoff: Optional[float] = Field(0.0, description="X 方向偏移量，默认 0.0")
    yoff: Optional[float] = Field(0.0, description="Y 方向偏移量，默认 0.0")

class TranslateResponse(BaseModel):
    code: int
    data: str  # 返回平移后的 GeoJSON 字符串
    message: str

@app.post("/translate", response_model=TranslateResponse)
def translate_api(req: TranslateRequest):
    """
    对 Overpass API 返回的 GeoJSON 数据中的几何对象进行平移。

    请求参数:
    - geojson_str: 输入的 GeoJSON 字符串
    - xoff: x 方向偏移量，默认 0.0
    - yoff: y 方向偏移量，默认 0.0

    返回:
    - code: 0 表示成功
    - data: 平移后的 GeoJSON 字符串
    - message: 结果信息
    """
    try:
        translated_geojson = translate(req.geojson_str, xoff=req.xoff, yoff=req.yoff)
        return TranslateResponse(code=0, data=translated_geojson, message="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"平移失败: {str(e)}")

class UnionRequest(BaseModel):
    geojson_str1: str = Field(..., description="第一个 GeoJSON 字符串")
    geojson_str2: str = Field(..., description="第二个 GeoJSON 字符串")

class UnionResponse(BaseModel):
    code: int
    data: str  # 返回并集后的 GeoJSON 字符串
    message: str

@app.post("/union", response_model=UnionResponse)
def union_api(req: UnionRequest):
    """
    计算 Overpass API 获取的两个 GeoJSON 数据的并集（union）。

    请求参数:
    - geojson_str1: 第一个 GeoJSON 字符串
    - geojson_str2: 第二个 GeoJSON 字符串

    返回:
    - code: 状态码，0 表示成功
    - data: 并集后的 GeoJSON 字符串
    - message: 返回信息
    """
    try:
        result_geojson = union(req.geojson_str1, req.geojson_str2)
        return UnionResponse(code=0, data=result_geojson, message="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"计算并集失败: {str(e)}")

class WithinRequest(BaseModel):
    geojson_str: str = Field(..., description="需要判断的 GeoJSON 字符串")
    container_geojson_str: str = Field(..., description="作为容器的 GeoJSON 字符串")

class WithinResponse(BaseModel):
    code: int
    data: List[bool]  # 每个 geometry 是否在容器内的布尔列表
    message: str

@app.post("/within", response_model=WithinResponse)
def within_api(req: WithinRequest):
    """
    判断 Overpass API 获取的 GeoJSON 数据中的几何对象是否完全包含在另一个几何对象内部。

    请求参数:
    - geojson_str: 需要判断的 GeoJSON 字符串
    - container_geojson_str: 作为容器的 GeoJSON 字符串

    返回:
    - code: 状态码，0 表示成功
    - data: 每个 geometry 是否在容器内的布尔列表
    - message: 返回信息
    """
    try:
        result = within(req.geojson_str, req.container_geojson_str)
        return WithinResponse(code=0, data=result, message="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"判断失败: {str(e)}")
