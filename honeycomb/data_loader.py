# -*- coding: utf-8 -*-
"""
数据加载模块
"""

import pandas as pd
from utils import logger

def read_weibo_excel(file_path):
    """读取并预处理微博Excel数据"""
    try:
        df = pd.read_excel(file_path)
        logger.info(f"成功读取文件，共 {len(df)} 条原始数据")

        # 确保必需列存在
        required_cols = ['经度', '纬度', '影响分类', '发布时间']
        for col in required_cols:
            if col not in df.columns:
                logger.error(f"必需列 '{col}' 不存在")
                return None

        # 确保经纬度和影响分类是数值类型
        df['经度'] = pd.to_numeric(df['经度'], errors='coerce')
        df['纬度'] = pd.to_numeric(df['纬度'], errors='coerce')
        df['影响分类'] = pd.to_numeric(df['影响分类'], errors='coerce')

        # 转换发布时间为datetime类型
        df['发布时间'] = pd.to_datetime(df['发布时间'], errors='coerce')
        
        # 清理无效数据
        df = df.dropna(subset=['经度', '纬度', '影响分类', '发布时间'])
        logger.info(f"清理后剩余 {len(df)} 条有效数据")
        
        # 提取日期信息
        df['日期'] = df['发布时间'].dt.date
        df['小时'] = df['发布时间'].dt.hour
        
        return df

    except Exception as e:
        logger.error(f"读取Excel文件失败: {e}")
        return None