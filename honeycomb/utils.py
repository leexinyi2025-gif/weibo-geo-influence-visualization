# -*- coding: utf-8 -*-
"""
工具函数模块
"""

import os
import logging
import json
import math
import pyproj
from shapely.ops import transform
from functools import partial

# 配置日志
def setup_logger(name=__name__):
    """设置并返回日志记录器"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def safe_mkdir(path):
    """安全创建目录"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger.warning(f"创建目录失败: {e}")
        return False

def load_json_file(file_path):
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载JSON文件失败: {e}")
        return None

def save_json_file(data, file_path):
    """保存数据到JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存JSON文件失败: {e}")
        return False

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
    
    return points

def get_coordinate_transformers():
    """获取坐标转换器"""
    wgs84 = pyproj.CRS('EPSG:4326')  # WGS84 (经纬度)
    utm50n = pyproj.CRS('EPSG:32650')  # UTM zone 50N (米)
    transformer_to_utm = pyproj.Transformer.from_crs(wgs84, utm50n, always_xy=True).transform
    transformer_to_wgs = pyproj.Transformer.from_crs(utm50n, wgs84, always_xy=True).transform
    
    return transformer_to_utm, transformer_to_wgs

# 全局日志记录器
logger = setup_logger(__name__)