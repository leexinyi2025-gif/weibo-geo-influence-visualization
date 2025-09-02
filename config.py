import os

# 默认配置
DEFAULT_CONFIG = {
    'input_file': os.path.join(os.getcwd(), 'data', 'combined_data.xlsx'),
    'output_dir': os.path.join(os.getcwd(), 'output'),
    'boundary_file': os.path.join(os.getcwd(), 'data', 'beijing_districts.geojson'),
    'hex_size': 500,  # 六边形边长（米）
    'target_districts': ['海淀区', '朝阳区', '东城区', '西城区', '石景山区', '丰台区'],
    'amap_tiles': 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}',
    'amap_attr': '高德地图'
}

def load_config(args):
    """加载配置，优先使用命令行参数，其次使用默认配置"""
    config = DEFAULT_CONFIG.copy()
    
    if args.input_file:
        config['input_file'] = args.input_file
    if args.output_dir:
        config['output_dir'] = args.output_dir
    if args.boundary_file:
        config['boundary_file'] = args.boundary_file
    if args.hex_size:
        config['hex_size'] = args.hex_size
    
    return config