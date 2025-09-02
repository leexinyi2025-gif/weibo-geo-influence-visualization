#!/usr/bin/env python3
"""
微博地理位置影响程度可视化工具 - 主程序
"""

import os
import argparse
import logging
import webbrowser
from datetime import datetime

from backend.data_loader import read_weibo_excel, filter_data_by_date
from backend.hexagon_grid import calculate_hexagon_influence
from backend.map_generator import create_influence_map
from backend.time_slider import create_time_slider_map
from backend.utils import setup_logging, safe_mkdir
from config import load_config

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='微博地理位置影响程度可视化工具')
    parser.add_argument('-i', '--input-file', help='输入Excel文件路径')
    parser.add_argument('-o', '--output-dir', help='输出目录路径')
    parser.add_argument('-b', '--boundary-file', help='边界GeoJSON文件路径')
    parser.add_argument('-s', '--hex-size', type=int, help='六边形边长（米）')
    parser.add_argument('-sd', '--start-date', help='开始日期（格式: YYYY-MM-DD）')
    parser.add_argument('-ed', '--end-date', help='结束日期（格式: YYYY-MM-DD）')
    parser.add_argument('-d', '--debug', action='store_true', help='启用调试模式')
    parser.add_argument('-nw', '--no-web', action='store_true', help='不自动打开浏览器')
    
    return parser.parse_args()

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logging(log_level)
    
    # 加载配置
    config = load_config(args)
    
    # 检查输入文件是否存在
    if not os.path.exists(config['input_file']):
        logger.error(f"输入文件不存在: {config['input_file']}")
        return
    
    # 创建输出目录
    safe_mkdir(config['output_dir'])
    
    # 读取和处理数据
    logger.info(f"开始处理文件: {config['input_file']}")
    df = read_weibo_excel(config['input_file'])
    
    if df is None:
        logger.error("数据处理失败，无法生成地图")
        return
    
    # 按日期过滤数据
    if args.start_date or args.end_date:
        df = filter_data_by_date(df, args.start_date, args.end_date)
        logger.info(f"日期过滤后剩余 {len(df)} 条数据")
    
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
            hex_size_meters=config['hex_size'],
            boundary_file=config['boundary_file'],
            target_districts=config['target_districts']
        )
        
        if hex_gdf is not None:
            # 生成当天地图
            map_filename = f"beijing_hexagon_honeycomb_map_{date_str}.html"
            map_file = os.path.join(config['output_dir'], map_filename)
            
            map_file = create_influence_map(
                hex_gdf, 
                map_file,
                boundary_file=config['boundary_file'],
                date_str=date_str,
                amap_tiles=config['amap_tiles']
            )
            
            if map_file:
                daily_maps[date_str] = f"file://{os.path.abspath(map_file)}"
                logger.info(f"日期 {date_str} 的地图已生成")
        else:
            logger.error(f"日期 {date_str} 的六边形网格计算失败")
    
    # 创建带时间滑块的主地图
    if daily_maps:
        time_slider_map = create_time_slider_map(daily_maps, config['output_dir'])
        if time_slider_map and not args.no_web:
            logger.info(f"成功生成时间滑块地图，尝试在浏览器中打开...")
            try:
                webbrowser.open(f"file://{os.path.abspath(time_slider_map)}")
            except Exception as e:
                logger.warning(f"无法自动打开浏览器: {e}")
                print(f"请手动打开生成的时间滑块地图文件: {os.path.abspath(time_slider_map)}")
    else:
        logger.error("没有成功生成任何日期的地图")

if __name__ == '__main__':
    main()