import os
import json
import logging

logger = logging.getLogger(__name__)

def create_time_slider_map(daily_maps, output_dir):
    """创建带时间滑块的主页面"""
    try:
        sorted_dates = sorted(daily_maps.keys())

        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>北京微博影响度时间轴</title>
    <style>
        body,html{{margin:0;height:100%;overflow:hidden;}}
        #mapFrame{{width:100%;height:100%;border:none;}}
        #timeSlider{{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);
                     background:white;padding:15px;border-radius:5px;
                     box-shadow:0 0 10px rgba(0,0,0,0.3);width:80%;max-width:600px;z-index:9999;}}
        button{{padding:6px 12px;margin:0 5px;cursor:pointer}}
        input[type=range]{{width:100%}}
    </style>
</head>
<body>
<iframe id="mapFrame" src="{daily_maps[sorted_dates[0]]}"></iframe>

<div id="timeSlider">
  <h4 style="margin:0 0 10px 0;text-align:center;">时间轴 - 选择日期查看影响分布</h4>
  <div style="display:flex;align-items:center;justify-content:space-between;">
    <button onclick="changeDate(-1)">前一天</button>
    <div style="flex-grow:1;margin:0 15px;">
      <input type="range" id="dateSlider" min="0" max="{len(sorted_dates)-1}" value="0" step="1"
             oninput="updateDateDisplay()">
      <div id="dateDisplay" style="text-align:center;font-weight:bold;">{sorted_dates[0]}</div>
    </div>
    <button onclick="changeDate(1)">后一天</button>
  </div>
  <div style="text-align:center;margin-top:10px;">
    <button onclick="playAnimation()" style="background:#28a745;color:white;border:none;border-radius:4px;">播放动画</button>
    <button onclick="stopAnimation()" style="background:#dc3545;color:white;border:none;border-radius:4px;">停止动画</button>
  </div>
</div>

<script>
const dailyMaps = {json.dumps(daily_maps)};
const sortedDates = {json.dumps(sorted_dates)};
let current = 0;
let timer = null;

function updateMap() {{
    document.getElementById('mapFrame').src = dailyMaps[sortedDates[current]];
    document.getElementById('dateDisplay').textContent = sortedDates[current];
    document.getElementById('dateSlider').value = current;
}}
function changeDate(d) {{
    current = Math.max(0, Math.min(sortedDates.length-1, current+d));
    updateMap();
}}
function updateDateDisplay() {{
    current = parseInt(document.getElementById('dateSlider').value);
    updateMap();
}}
function playAnimation() {{
    stopAnimation();
    timer = setInterval(()=>{{
        current = (current+1) % sortedDates.length;
        updateMap();
    }}, 2000);
}}
function stopAnimation() {{
    if (timer) {{clearInterval(timer); timer=null;}}
}}
</script>
</body>
</html>'''

        slider_file = os.path.join(output_dir, "beijing_time_slider_map.html")
        with open(slider_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"时间滑块主页面已保存到: {slider_file}")
        return slider_file

    except Exception as e:
        logger.error(f"生成时间滑块页面失败: {e}")
        return None