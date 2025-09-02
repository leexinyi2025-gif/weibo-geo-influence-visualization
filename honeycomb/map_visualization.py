# -*- coding: utf-8 -*-
"""
地图可视化模块
"""

import folium
import branca.colormap as cm
import glob
import json
import os

from utils import logger, safe_mkdir, load_json_file, save_json_file
from config import DEFAULT_CONFIG

def read_beijing_boundary(boundary_file, target_districts=None):
    """读取北京边界GeoJSON文件，返回经纬度点列表，可指定特定区域"""
    try:
        if not boundary_file or not os.path.exists(boundary_file):
            logger.warning("边界文件不存在，跳过绘制")
            return []
            
        geo = load_json_file(boundary_file)
        if not geo:
            return []
            
        boundary_points = []
        for feature in geo['features']:
            if target_districts:
                district_name = feature['properties'].get('name', '')
                if district_name not in target_districts:
                    continue
                    
            geometry = feature['geometry']
            if geometry['type'] == 'Polygon':
                for ring in geometry['coordinates']:
                    ring_points = [[lat, lng] for lng, lat in ring]
                    boundary_points.append(ring_points)
            elif geometry['type'] == 'MultiPolygon':
                for polygon in geometry['coordinates']:
                    for ring in polygon:
                        ring_points = [[lat, lng] for lng, lat in ring]
                        boundary_points.append(ring_points)
        logger.info(f"成功读取边界文件，共 {len(boundary_points)} 个边界多边形")
        return boundary_points
    except Exception as e:
        logger.error(f"读取边界文件失败: {e}")
        return []

def add_boundary_to_map(m, boundary_file, target_districts=None):
    """将边界添加到地图，避免重叠"""
    if target_districts is None:
        target_districts = DEFAULT_CONFIG['target_districts']
        
    boundary_polygons = read_beijing_boundary(boundary_file, target_districts)
    if not boundary_polygons:
        logger.warning("边界点为空，跳过绘制")
        return
    
    district_colors = {
        '海淀区': '#FF6B6B',
        '朝阳区': '#4ECDC4',
        '东城区': '#45B7D1',
        '西城区': '#96CEB4',
        '石景山区': '#FFEAA7',
        '丰台区': '#DDA0DD'
    }
    
    for i, polygon_points in enumerate(boundary_polygons):
        color = district_colors.get(target_districts[i] if i < len(target_districts) else '未知区域', 'blue')
            
        folium.PolyLine(
            polygon_points,
            color=color,
            weight=3,
            opacity=0.8,
            fill=False,
            tooltip=f'北京精准边界 - {target_districts[i] if i < len(target_districts) else "未知区域"}'
        ).add_to(m)
    
    logger.info("成功添加精准边界到地图")

def create_influence_map(hex_gdf, output_path, boundary_file=None, date_str=None, config=None):
    """创建六边形影响力地图"""
    if config is None:
        config = DEFAULT_CONFIG
        
    try:
        # 生成网格可视化图
        grid_image_path = visualize_hexagon_grid(hex_gdf, config['hex_size_meters'])
        grid_image_url = f"file://{os.path.abspath(grid_image_path)}" if grid_image_path else ""

        # 收集所有日期的hex_data
        hex_data_dict = {}
        output_dir = os.path.dirname(output_path) if os.path.isdir(output_path) else output_path
        json_files = glob.glob(os.path.join(output_dir, "beijing_hexagon_honeycomb_map_*.json"))
        for jf in json_files:
            date_part = os.path.basename(jf).replace("beijing_hexagon_honeycomb_map_","").replace(".json","")
            try:
                hex_data_dict[date_part] = load_json_file(jf)
            except Exception:
                continue
        
        # 当前日期
        hex_data = []
        for _, row in hex_gdf.iterrows():
            center = row['geometry'].centroid
            hex_data.append({
                'lat': center.y,
                'lng': center.x,
                'star': int(row['star_rating']),
                'max_level': int(row['max_level']),
                'count': int(row['count']),
                'row': int(row['row']),
                'col': int(row['col'])
            })
            
        if date_str:
            hex_data_dict[date_str] = hex_data
            
        if not hex_data_dict:
            hex_data_dict[date_str if date_str else '当前'] = hex_data
            
        hex_data_dict_json = json.dumps(hex_data_dict, ensure_ascii=False)
        
        # 保存当前hex_data为json
        if date_str:
            try:
                save_json_file(hex_data, os.path.join(output_dir, f"beijing_hexagon_honeycomb_map_{date_str}.json"))
            except Exception:
                pass

        # 日期显示
        date_display = f" - {date_str}" if date_str else ""

        # 创建HTML内容，增加日期选择
        date_options = ''.join([f'<option value="{d}">{d}</option>' for d in sorted(hex_data_dict.keys())])
        search_html = f'''
        <div id="locationSearch" style="position: fixed; top: 10px; left: 10px; z-index: 1000; background: white; padding: 10px; border-radius: 5px; box-shadow: 0 0 5px rgba(0,0,0,0.3);">
            <h4 style="margin:0 0 10px 0;">区域影响查询</h4>
            <select id="dateSelect" style="margin-bottom:5px; width: 140px;">
                {date_options}
            </select>
            <input type="text" id="coordInput" placeholder="输入经纬度，如: 39.90, 116.40" style="width: 180px; padding: 5px; margin-right: 5px;">
            <button onclick="searchLocation()" style="padding: 5px 10px;">查询</button>
            <div id="resultPanel" style="margin-top: 10px; display: none; border-top: 1px solid #eee; padding-top: 10px;">
                <div><strong>查询结果:</strong></div>
                <div id="resultContent" style="margin-top: 5px;"></div>
            </div>
        </div>
        <div id="gridInfo" style="position: fixed; top: 10px; right: 10px; z-index: 1000; background: white; padding: 10px; border-radius: 5px; box-shadow: 0 0 5px rgba(0,0,0,0.3); max-width: 300px;">
            <h4 style="margin:0 0 10px 0;">网格信息{date_display}</h4>
            <p>六边形数量: {len(hex_gdf)}</p>
            <p>边长: {config['hex_size_meters']}米</p>
            <p>排列方式: 蜂窝状错位</p>
            <img src="{grid_image_url}" alt="网格结构" style="width:100%; margin-top:10px; border:1px solid #eee;">
        </div>
        <script>
        const hexDataDict = {hex_data_dict_json};
        let hexData = hexDataDict[Object.keys(hexDataDict)[0]];
        document.getElementById('dateSelect').addEventListener('change', function() {{
            const d = this.value;
            hexData = hexDataDict[d] || [];
        }});
        function haversineDistance(lat1, lng1, lat2, lng2) {{
            const R = 6371000;
            const dLat = (lat2 - lat1) * Math.PI / 180;
            const dLng = (lng2 - lng1) * Math.PI / 180;
            const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                      Math.sin(dLng/2) * Math.sin(dLng/2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
            return R * c;
        }}
        function findNearestHex(lat, lng) {{
            let minDist = Number.MAX_VALUE;
            let nearestHex = null;
            for (const hex of hexData) {{
                const dist = haversineDistance(lat, lng, hex.lat, hex.lng);
                if (dist < minDist) {{
                    minDist = dist;
                    nearestHex = hex;
                }}
            }}
            return {{hex: nearestHex, distance: minDist}};
        }}
        const starDescriptions = {json.dumps(config['star_descriptions'], ensure_ascii=False)};
        const starColors = {json.dumps(config['star_colors'], ensure_ascii=False)};
        function searchLocation() {{
            const input = document.getElementById('coordInput').value;
            const coords = input.split(',').map(coord => parseFloat(coord.trim()));
            if (coords.length !== 2 || isNaN(coords[0]) || isNaN(coords[1])) {{
                alert('请输入有效的经纬度，格式如: 39.90, 116.40');
                return;
            }}
            const lat = parseFloat(coords[0].toFixed(6));
            const lng = parseFloat(coords[1].toFixed(6));
            if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {{
                alert('纬度范围应为-90到90，经度范围应为-180到180');
                return;
            }}
            const result = findNearestHex(lat, lng);
            const hex = result.hex;
            const distance = result.distance.toFixed(0);
            const resultPanel = document.getElementById('resultPanel');
            const resultContent = document.getElementById('resultContent');
            if (hex) {{
                const starSymbol = '★'.repeat(hex.star);
                const starColor = starColors[hex.star] || 'black';
                resultContent.innerHTML = `
                    <div style="margin-bottom: 8px;">
                        <span style="font-weight:bold; color:${{starColor}};">${{starSymbol}} ${{starDescriptions[hex.star]}}</span>
                    </div>
                    <div><strong>位置:</strong> (${{hex.lat.toFixed(6)}}, ${{hex.lng.toFixed(6)}})</div>
                    <div><strong>距离查询点:</strong> ${{distance}} 米</div>
                    <div><strong>影响分类等级:</strong> ${{hex.max_level}}（${{hex.star}}星）</div>
                    <div><strong>微博数量:</strong> ${{hex.count}}</div>
                    <div><strong>网格位置:</strong> 行 ${{hex.row}} 列 ${{hex.col}}</div>
                `;
                resultPanel.style.display = 'block';
            }} else {{
                resultContent.innerHTML = '<div style="color:red;">未找到附近的六边形数据</div>';
                resultPanel.style.display = 'block';
            }}
        }}
        </script>
        <style>
            #locationSearch input:focus {{ outline: 2px solid #4A90E2; }}
            #resultContent div {{ margin-bottom: 3px; }}
            #gridInfo img {{ transition: transform 0.3s; }}
            #gridInfo img:hover {{ transform: scale(1.5); }}
        </style>
        '''
        
        # 计算中心点
        center = hex_gdf.unary_union.centroid
        center_lat, center_lng = center.y, center.x
        logger.info(f"地图中心点: 纬度 {center_lat:.6f}, 经度 {center_lng:.6f}")
        
        # 计算缩放级别
        bounds = hex_gdf.unary_union.bounds
        lat_diff = bounds[3] - bounds[1]
        zoom_start = 11 if lat_diff < 0.3 else 10 if lat_diff < 0.6 else 9
        
        # 创建基础地图 - 使用高德地图作为底图
        amap_tiles = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}'
        amap_attr = '高德地图'
        
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=zoom_start,
            tiles=amap_tiles,
            attr=amap_attr,
            control_scale=True
        )

        # 自动适配所有六边形区域
        try:
            bounds = hex_gdf.unary_union.bounds
            fit_bounds = [[bounds[1], bounds[0]], [bounds[3], bounds[2]]]
            m.fit_bounds(fit_bounds)
        except Exception as e:
            logger.warning(f"fit_bounds 自动适配失败: {e}")

        # 添加搜索框和网格信息
        m.get_root().html.add_child(folium.Element(search_html))
        
        # 创建莫兰迪色系颜色映射
        colormap = cm.LinearColormap(
            colors=list(config['star_colors'].values()),
            index=list(config['star_colors'].keys()),
            vmin=0,
            vmax=4,
            caption='影响程度（0-4星莫兰迪色系）'
        )
        colormap.add_to(m)
        
        # 添加北京边界
        add_boundary_to_map(m, boundary_file, config['target_districts'])
        
        # 添加六边形区域
        for idx, row in hex_gdf.iterrows():
            try:
                star = int(row['star_rating'])
                color = colormap(star)
                count = int(row['count'])
                
                # 获取六边形边界坐标
                hex_boundary = list(row['geometry'].exterior.coords)
                hex_boundary = [(y, x) for x, y in hex_boundary]
                
                # 创建弹出窗口内容
                center = row['geometry'].centroid
                popup_content = f"""
                <div style="width:250px;">
                    <h4>六边形区域 #{row['hex_id']}</h4>
                    <hr>
                    <p><b>位置:</b> 行 {row['row']} 列 {row['col']}</p>
                    <p><b>影响分类等级:</b> {star}星）</p>
                    <p><b>微博数量:</b> {count}</p>
                    <p><b>中心位置:</b> ({center.y:.6f}, {center.x:.6f})</p>
                </div>
                """
                
                # 添加六边形多边形
                folium.Polygon(
                    locations=hex_boundary,
                    color='#555555',
                    weight=1,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7,
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"影响等级: {star}星"
                ).add_to(m)
                
            except Exception as e:
                logger.warning(f"添加六边形 #{row['hex_id']} 时出错: {e}")
                continue
        
        # 保存地图
        if not safe_mkdir(output_path):
            output_path = os.getcwd()
            logger.info(f"使用当前目录作为输出路径: {output_path}")
        
        # 如果有日期信息，添加到文件名中
        if date_str:
            map_file = os.path.join(output_path, f"beijing_hexagon_honeycomb_map_{date_str}.html")
        else:
            map_file = os.path.join(output_path, "beijing_hexagon_honeycomb_map.html")
            
        m.save(map_file)
        logger.info(f"地图已保存到: {map_file}")
        return map_file
    except Exception as e:
        logger.error(f"生成地图时发生致命错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None