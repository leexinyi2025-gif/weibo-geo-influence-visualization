# -*- coding: utf-8 -*-
"""
六边形网格处理模块
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
import matplotlib.pyplot as plt

from utils import logger, create_pointy_top_hexagon, get_coordinate_transformers
from config import DEFAULT_CONFIG

def get_neighbors(row, col):
    """用立方体坐标求尖顶六边形 6 个邻居"""
    q = col
    r = row - (col - (col & 1)) // 2
    s = -q - r

    directions = [
        (+1, -1,  0), (+1,  0, -1), ( 0, +1, -1),
        (-1, +1,  0), (-1,  0, +1), ( 0, -1, +1)
    ]
    neighbors = []
    for dq, dr, ds in directions:
        nq, nr, ns = q + dq, r + dr, s + ds
        ncol = nq
        nrow = nr + (nq - (nq & 1)) // 2
        neighbors.append((nrow, ncol))
    return [(r, c) for r, c in neighbors if r >= 0 and c >= 0]

def load_beijing_boundary(boundary_file, target_districts=None):
    """加载北京边界并创建多边形，可指定特定区域"""
    try:
        if not boundary_file or not os.path.exists(boundary_file):
            logger.warning("边界文件不存在，跳过边界裁剪")
            return None
        
        geo = load_json_file(boundary_file)
        if not geo:
            return None
        
        polygons = []
        for feature in geo['features']:
            if target_districts:
                district_name = feature['properties'].get('name', '')
                if district_name not in target_districts:
                    continue
            
            geometry = feature['geometry']
            if geometry['type'] == 'Polygon':
                for ring in geometry['coordinates']:
                    ring_points = [(lng, lat) for lng, lat in ring]
                    polygons.append(Polygon(ring_points))
            elif geometry['type'] == 'MultiPolygon':
                for polygon in geometry['coordinates']:
                    for ring in polygon:
                        ring_points = [(lng, lat) for lng, lat in ring]
                        polygons.append(Polygon(ring_points))
        
        beijing_poly = unary_union(polygons)
        logger.info(f"成功加载北京边界，共 {len(polygons)} 个多边形")
        return beijing_poly
    
    except Exception as e:
        logger.error(f"加载边界文件失败: {e}")
        return None

def calculate_hexagon_influence(df, hex_size_meters=500, boundary_file=None, target_districts=None):
    """计算六边形网格影响力（使用投影坐标系确保正六边形）"""
    try:
        logger.info(f"开始创建北京区域蜂窝状六边形网格（边长={hex_size_meters}米）...")
        
        if target_districts is None:
            target_districts = DEFAULT_CONFIG['target_districts']
        
        # 加载北京边界
        beijing_poly = load_beijing_boundary(boundary_file, target_districts)
        
        # 获取坐标转换器
        transformer_to_utm, transformer_to_wgs = get_coordinate_transformers()

        # 投影北京边界到UTM
        if beijing_poly:
            beijing_utm = transform(transformer_to_utm, beijing_poly)
            min_x, min_y, max_x, max_y = beijing_utm.bounds
            
            # 扩大边界范围，确保完全覆盖
            expand_margin = 5000
            min_x -= expand_margin
            min_y -= expand_margin
            max_x += expand_margin
            max_y += expand_margin
        else:
            # 如果没有边界，使用数据范围
            min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')
            for lng, lat in zip(df['经度'], df['纬度']):
                x, y = transformer_to_utm(lng, lat)
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
            
            expand_margin = 5000
            min_x -= expand_margin
            min_y -= expand_margin
            max_x += expand_margin
            max_y += expand_margin
            
            logger.warning("未提供边界文件，使用数据范围创建网格")
        
        # 计算六边形参数（在投影坐标系中）
        horizontal_spacing = hex_size_meters * 1.5
        vertical_spacing = hex_size_meters * math.sqrt(3)
        y_shift = hex_size_meters * math.sqrt(3) / 2

        # 计算列数和行数
        num_cols = int((max_x - min_x) / horizontal_spacing) + 5
        num_rows = int((max_y - min_y) / vertical_spacing) + 5

        logger.info(f"网格范围: X({min_x:.1f}-{max_x:.1f}), Y({min_y:.1f}-{max_y:.1f})")
        logger.info(f"网格尺寸: {num_cols}列 x {num_rows}行")

        hexagons = []
        hex_id = 0
        for col in range(num_cols):
            x_offset = min_x + col * horizontal_spacing
            for row in range(num_rows):
                if col % 2 == 0:
                    y_offset = min_y + row * vertical_spacing
                else:
                    y_offset = min_y + row * vertical_spacing + y_shift

                # 创建六边形
                hex_points_utm = create_pointy_top_hexagon(x_offset, y_offset, hex_size_meters)
                hexagon_utm = Polygon(hex_points_utm)

                # 检查六边形中心是否在北京边界内
                center_point = Point(x_offset, y_offset)
                if beijing_utm is None or beijing_utm.contains(center_point):
                    # 将六边形转换回WGS84坐标系
                    hex_points_wgs84 = [transformer_to_wgs(x, y) for x, y in hex_points_utm]
                    hexagon_wgs84 = Polygon(hex_points_wgs84)

                    # 获取中心点
                    center = hexagon_wgs84.centroid

                    hexagons.append({
                        'hex_id': hex_id,
                        'geometry': hexagon_wgs84,
                        'center_lng': center.x,
                        'center_lat': center.y,
                        'row': row,
                        'col': col
                    })
                    hex_id += 1
        
        logger.info(f"创建了 {len(hexagons)} 个六边形")
        
        # 创建六边形GeoDataFrame
        hex_gdf = gpd.GeoDataFrame(hexagons, geometry='geometry', crs="EPSG:4326")
        
        # 创建微博点GeoDataFrame
        geometry = [Point(lng, lat) for lng, lat in zip(df['经度'], df['纬度'])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
        
        # 空间连接，计算每个六边形内的点
        if len(hex_gdf) > 0:
            joined = gpd.sjoin(gdf, hex_gdf, how="inner", predicate='within')
            
            # 计算每个六边形的统计信息
            hex_stats = joined.groupby('hex_id').agg(
                max_level=('影响分类', 'max'),
                count=('影响分类', 'count'),
                lv2_cnt=('影响分类', lambda s: (s == 2).sum()),
                lv3_cnt=('影响分类', lambda s: (s == 3).sum())
            ).reset_index()

            hex_stats['lv2_plus_lv3'] = hex_stats['lv2_cnt'] + hex_stats['lv3_cnt']
                        
            # 合并回六边形GeoDataFrame
            hex_gdf = hex_gdf.merge(hex_stats, on='hex_id', how='left')
            
            # 填充空值
            for col in ['max_level', 'count', 'lv2_cnt', 'lv3_cnt', 'lv2_plus_lv3']:
                hex_gdf[col] = hex_gdf[col].fillna(0)
            
            # 计算星级
            def star_rating(row):
                if pd.isna(row['lv2_plus_lv3']):
                    return 0
                if row['lv2_plus_lv3'] > 5:
                    return 4
                return min(3, int(row['max_level'] or 0))
            
            hex_gdf['star_rating'] = hex_gdf.apply(star_rating, axis=1)
            
            # 处理邻居关系
            row_col_to_id = {}
            for idx, row in hex_gdf.iterrows():
                row_col_to_id[(row['row'], row['col'])] = row['hex_id']
            
            hex_info = {}
            for idx, row in hex_gdf.iterrows():
                hex_id = row['hex_id']
                hex_info[hex_id] = {
                    'star_rating': row['star_rating'],
                    'row': row['row'],
                    'col': row['col'],
                    'neighbors': []
                }
            
            for hex_id, info in hex_info.items():
                neighbors = get_neighbors(info['row'], info['col'])
                for nr, nc in neighbors:
                    if (nr, nc) in row_col_to_id:
                        neighbor_id = row_col_to_id[(nr, nc)]
                        info['neighbors'].append(neighbor_id)
            
            # 邻居提升规则
            updates = {}
            for hex_id, info in hex_info.items():
                star = info['star_rating']
                for neighbor_id in info['neighbors']:
                    nstar = hex_info[neighbor_id]['star_rating']
                    if star == 4:
                        if nstar == 0 or nstar == 1:
                            if neighbor_id not in updates or updates[neighbor_id] < 2:
                                updates[neighbor_id] = 2
                        elif nstar == 2:
                            updates[neighbor_id] = 3
                    elif star == 3:
                        if nstar == 0:
                            if neighbor_id not in updates or updates[neighbor_id] < 1:
                                updates[neighbor_id] = 1
                        elif nstar == 1:
                            if neighbor_id not in updates or updates[neighbor_id] < 2:
                                updates[neighbor_id] = 2

            for hex_id, new_star in updates.items():
                hex_gdf.loc[hex_gdf['hex_id'] == hex_id, 'star_rating'] = new_star
            logger.info(f"已更新 {len(updates)} 个区域的星级（邻居提升）")
        else:
            # 如果没有数据，设置默认值
            for col in ['max_level', 'count', 'lv2_cnt', 'lv3_cnt', 'lv2_plus_lv3', 'star_rating']:
                hex_gdf[col] = 0
        
        logger.info(f"北京区域蜂窝状六边形网格创建完成，共 {len(hex_gdf)} 个六边形区域")
        logger.info(f"星级分布: {hex_gdf['star_rating'].value_counts().to_dict()}")
        
        return hex_gdf
    
    except Exception as e:
        logger.error(f"计算六边形网格时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def visualize_hexagon_grid(hex_gdf, hex_size):
    """可视化六边形网格质量"""
    try:
        fig, ax = plt.subplots(figsize=(15, 12))
        
        for idx, row in hex_gdf.iterrows():
            hexagon = row['geometry']
            x, y = hexagon.exterior.xy
            ax.plot(x, y, 'b-', linewidth=0.8, alpha=0.7)
            
            center = hexagon.centroid
            ax.plot(center.x, center.y, 'ro', markersize=2)
            
            info = f"ID:{row['hex_id']}\nR:{row['row']} C:{row['col']}"
            ax.text(center.x, center.y, info, fontsize=6, ha='center', va='center')
        
        plt.title(f'蜂窝状六边形网格 (边长={hex_size}米)', fontsize=16)
        plt.xlabel('经度', fontsize=12)
        plt.ylabel('纬度', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.5)
        
        output_path = os.path.join(os.getcwd(), "hexagon_honeycomb_grid.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"六边形网格可视化已保存到: {output_path}")
        
        plt.close()
        return output_path
        
    except Exception as e:
        logger.error(f"六边形网格可视化失败: {e}")
        return None