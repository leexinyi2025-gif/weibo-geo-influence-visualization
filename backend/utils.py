import os
import logging
import json
import math
from functools import partial
from shapely.ops import unary_union, transform
import pyproj
from shapely.geometry import Polygon, Point
import geopandas as gpd

# 配置日志
def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def safe_mkdir(path):
    """安全创建目录"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logging.warning(f"创建目录失败: {e}")
        return False

def load_geojson(file_path):
    """加载GeoJSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"加载GeoJSON文件失败: {e}")
        return None

def create_pointy_top_hexagon(center_x, center_y, size_meters):
    """
    创建尖顶六边形（在投影坐标系中）
    size_meters: 六边形边长（米）
    """
    points = []
    for i in range(6):
        angle_deg = 60 * i
        angle_rad = math.radians(angle_deg)
        x = center_x + size_meters * math.cos(angle_rad)
        y = center_y + size_meters * math.sin(angle_rad)
        points.append((x, y))
    return Polygon(points)

def get_neighbors(row, col):
    """
    用立方体坐标求尖顶六边形 6 个邻居
    """
    q = col
    r = row - (col - (col & 1)) // 2
    s = -q - r

    directions = [
        (+1, -1, 0), (+1, 0, -1), (0, +1, -1),
        (-1, +1, 0), (-1, 0, +1), (0, -1, +1)
    ]
    neighbors = []
    for dq, dr, ds in directions:
        nq, nr, ns = q + dq, r + dr, s + ds
        ncol = nq
        nrow = nr + (nq - (nq & 1)) // 2
        neighbors.append((nrow, ncol))
    return [(r, c) for r, c in neighbors if r >= 0 and c >= 0]

def create_transformer(from_crs, to_crs):
    """创建坐标转换器"""
    return pyproj.Transformer.from_crs(
        pyproj.CRS(from_crs), 
        pyproj.CRS(to_crs), 
        always_xy=True
    ).transform