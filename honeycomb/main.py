# -*- coding: utf-8 -*-
"""
主程序 - 微博地理位置影响程度可视化工具
"""

import os
import webbrowser
from datetime import datetime

from data_loader import read_weibo_excel
from hexagon_grid import calculate_hexagon_influence
from map_visualization import create_influence_map
from time_slider import create_time_slider_map
from utils import logger
from config import DEFAULT_CONFIG

def main():
    # 使用配置
    config = DEFAULT_CONFIG
    
    # 处理文件路径
    if not os.path.exists(config['input_file']):
        logger.error(f"输入文件不存在: {config['input_file']}")
        logger.info("请确保Excel文件与脚本在同一目录下，或提供完整路径")
        return
    
    # 读取和处理数据
    logger.info(f"开始处理文件: {config['input_file']}")
    df = read_weibo_excel(config['input_file'])
    if df is not None:
        logger.info(f"数据预览:\n{df[['地点名称', '经度', '纬度', '影响分类', '发布时间']].head()}")
        
        # 获取所有日期
        dates = sorted(df['日期'].unique())
        logger.info(f"数据包含以下日期: {[str(d) for d in dates]}")
        
        # 为每天创建单独的地图
        daily_maps = {}
        
        for date in dates:
            date_str = date.strftime("%Y-%m-%d")
            logger.info(f"处理日期 {date_str} 的数据...")
            
            # 筛选当天的数据
            day_df = df[df['日期'] == date]
            logger.info(f"日期 {date_str} 有 {len(day_df)} 条数据")
            
            # 使用六边形网格计算影响
            hex_gdf = calculate_hexagon_influence(
                day_df, 
                hex_size_meters=config['hex_size_meters'],
                boundary_file=config['boundary_file'],
                target_districts=config['target_districts']
            )
            
            if hex_gdf is not None:
                # 生成当天地图
                map_file = create_influence_map(
                    hex_gdf, 
                    config['output_dir'], 
                    boundary_file=config['boundary_file'],
                    date_str=date_str,
                    config=config
                )
                if map_file:
                    daily_maps[date_str] = f"file://{os.path.abspath(map_file)}"
                    logger.info(f"日期 {date_str} 的地图已生成")
            else:
                logger.error(f"日期 {date_str} 的六边形网格计算失败")
        
        # 创建带时间滑块的主地图
        if daily_maps:
            time_slider_map = create_time_slider_map(daily_maps, config['output_dir'], config['boundary_file'])
            if time_slider_map:
                logger.info(f"成功生成时间滑块地图，尝试在浏览器中打开...")
                try:
                    webbrowser.open(f"file://{os.path.abspath(time_slider_map)}")
                except Exception as e:
                    logger.warning(f"无法自动打开浏览器: {e}")
                    print(f"请手动打开生成的时间滑块地图文件: {os.path.abspath(time_slider_map)}")
        else:
            logger.error("没有成功生成任何日期的地图")
    else:
        logger.error("数据处理失败，无法生成地图")

if __name__ == '__main__':
    main()