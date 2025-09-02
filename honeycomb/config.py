# -*- coding: utf-8 -*-
"""
配置文件 - 微博地理位置影响程度可视化工具
"""

# 默认配置
DEFAULT_CONFIG = {
    'input_file': "C:\\Users\\大盈仙人\\Desktop\\大风微博数据\\combined_data_5.xlsx",
    'output_dir': "C:\\Users\\大盈仙人\\Desktop\\大风微博数据",
    'boundary_file': "C:\\Users\\大盈仙人\\Desktop\\大风真实数据\\beijing_districts.geojson",
    'hex_size_meters': 500,
    'target_districts': ['海淀区', '朝阳区', '东城区', '西城区', '石景山区', '丰台区'],
    'star_colors': {
        0: '#E0E0E0',  # Gray
        1: '#8CA6DB',  # Morandi Blue
        2: '#E6C27A',  # Morandi Yellow
        3: '#D99058',  # Dark Morandi Orange
        4: '#D9534F'   # Morandi Red
    },
    'star_descriptions': {
        0: "无数据区域",
        1: "1星区 (影响分类1)",
        2: "2星区 (影响分类2)",
        3: "3星区 (影响分类3)",
        4: "4星区 (二级+三级≥10)"
    }
}