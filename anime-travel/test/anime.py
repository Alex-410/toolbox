import requests
import json

OLLAMA_BASE_URL = "http://localhost:11434"

# ====================== 配置区（已全部填好） ======================
OPENROUTESERVICE_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6Ijc5ZmJhMDk2N2NjNDQ3ZDE4ODQzYzc2NmZkNGU3N2FhIiwiaCI6Im11cm11cjY0In0="
PROXY = {
    "http": "http://127.0.0.1:7892",
    "https": "http://127.0.0.1:7892"
}
OLLAMA_MODEL = "deepseek-r1:1.5b"
# ===================================================================

# 1. 模拟动漫圣地数据
def get_simulated_anime_locations():
    return [
        {
            "name": "须贺神社阶梯",
            "anime": "你的名字",
            "episode": "EP12 18:45",
            "address": "东京都新宿区须贺町5-1",
            "lat": 35.6945,
            "lon": 139.7182,
            "description": "三叶和泷最终相遇的阶梯"
        },
        {
            "name": "新宿警察署十字路口",
            "anime": "你的名字",
            "episode": "EP01 05:20",
            "address": "东京都新宿区西新宿2-8-1",
            "lat": 35.6896,
            "lon": 139.6983,
            "description": "泷每天上学经过的十字路口"
        },
        {
            "name": "国立新美术馆",
            "anime": "你的名字",
            "episode": "EP08 12:30",
            "address": "东京都港区六本木7-22-2",
            "lat": 35.6657,
            "lon": 139.7264,
            "description": "奥寺前辈和泷约会的咖啡馆"
        },
        {
            "name": "须贺神社鸟居",
            "anime": "天气之子",
            "episode": "EP10 25:10",
            "address": "东京都新宿区须贺町5-1",
            "lat": 35.6942,
            "lon": 139.7180,
            "description": "帆高和阳菜祈祷晴天的鸟居"
        },
        {
            "name": "代代木会馆",
            "anime": "天气之子",
            "episode": "EP05 15:40",
            "address": "东京都涩谷区代代木2-31-1",
            "lat": 35.6812,
            "lon": 139.7034,
            "description": "阳菜家所在的废弃大楼"
        },
        {
            "name": "东京站八重洲口",
            "anime": "铃芽之旅",
            "episode": "EP09 08:20",
            "address": "东京都千代田区丸之内1-9-1",
            "lat": 35.6812,
            "lon": 139.7671,
            "description": "铃芽和草太到达东京的车站"
        },
        {
            "name": "东京塔",
            "anime": "铃芽之旅",
            "episode": "EP11 19:30",
            "address": "东京都港区芝公园4-2-8",
            "lat": 35.6586,
            "lon": 139.7454,
            "description": "东京最大的闭门所在地"
        }
    ]

# 2. 最优路线规划（只有这个请求走代理）
def plan_optimal_route(locations, mode='foot-walking'):
    print("🗺️ 正在规划最优路线...")
    coordinates = [[loc['lon'], loc['lat']] for loc in locations]
    url = f"https://api.openrouteservice.org/v2/directions/{mode}"
    headers = {
        'Authorization': OPENROUTESERVICE_KEY,
        'Content-Type': 'application/json'
    }
    data = {
        "coordinates": coordinates,
        "language": "zh-CN",
        "instructions": True,
        "optimize_waypoints": True
    }
    try:
        # ✅ 关键修复：只有这个请求加代理
        response = requests.post(url, headers=headers, json=data, proxies=PROXY, timeout=30)
        result = response.json()
        if 'error' in result:
            print(f"⚠️ API报错，使用默认路线")
            return {"total_distance": 12.5,"total_duration": 180,"optimized_order": list(range(len(locations)))}
        route = result['routes'][0]
        return {
            "total_distance": round(route['summary']['distance'] / 1000, 1),
            "total_duration": round(route['summary']['duration'] / 60),
            "optimized_order": result['waypoints']
        }
    except Exception as e:
        print(f"⚠️ 网络异常，使用默认路线：{e}")
        return {"total_distance": 12.5,"total_duration": 180,"optimized_order": list(range(len(locations)))}

# 3. 本地Ollama生成路线（这个请求不走代理）
def generate_itinerary_with_ollama(anime_names, days, locations, route_info):
    print("🤖 正在调用本地Ollama生成路线规划...")
    prompt = f"""
你是专业动漫圣地巡礼规划师，严格按照格式输出，不许改动结构！

【基本信息】
- 涉及作品：{', '.join(anime_names)}
- 旅行天数：{days}天
- 总地标：{len(locations)}个
- 总距离：{route_info['total_distance']}公里
- 总时间：{route_info['total_duration']}分钟

【地标数据】
{json.dumps(locations, ensure_ascii=False, indent=2)}

【输出格式（严格照搬）】
# 多作品混合圣地巡礼路线规划（{days}日版）
## 整体规划说明
- 覆盖地标总数：{len(locations)}个
- 涉及作品：{', '.join([f'《{name}》' for name in anime_names])}
- 推荐出行方式：JR/地铁+步行
- 核心覆盖区域：东京都新宿区、涩谷区、港区、千代田区
- 推荐交通卡：Suica卡/东京地铁72小时券

---

## 第1天：新宿-涩谷区域巡礼
### 路线顺序：新宿站 → 地标1 → 地标2 → 地标3
### 当日总步行距离：约X公里 | 总耗时：约X小时

1. 【地标1：XX地点】
   - 作品出处：《作品名称》 EPX XX:XX
   - 地理坐标：北纬XX.XX 东经XX.XX
   - 现实地址：XX
   - 交通衔接：XX
   - 打卡建议：XX
   - 耗时预估：停留X分钟

### 第1天餐饮与休息建议
- 午餐推荐：XX
- 休息点：XX
- 晚餐推荐：XX

---

## 第2天：六本木-港区区域巡礼
（格式同上）

---

## 整体出行小贴士
### 交通建议
1. 推荐购买东京地铁72小时券
2. 公交准点，提前5分钟到站
3. 使用Google Maps/换乘案内

### 打卡建议
1. 按顺序打卡，不折返
2. 提前存动画截图
3. 热门点早9点前到

### 作品还原小贴士
1. 带道具拍照更有代入感
2. 观察建筑细节
3. 尊重当地居民

### 应急提示
1. 带好护照
2. 向车站/警察求助
3. 紧急电话：110 / 119

【规则】
1. 严格按格式输出
2. 只用给定数据，不编造
3. 分2天规划，每天3-4个地点
4. 打卡建议贴合动画场景
"""
    # ✅ 使用原生 requests 调用 Ollama API
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "你是严格遵守格式的规划师，只输出规划内容，无多余文字"},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    response = requests.post(url, json=payload, timeout=120)
    result = response.json()
    print(f"🔍 Ollama 响应状态: {response.status_code}")
    print(f"🔍 Ollama 响应内容: {result}")
    
    if 'message' not in result:
        raise Exception(f"Ollama API 错误: {result}")
    
    return result['message']['content']

# 4. 主程序
def main():
    ANIME_NAMES = ["你的名字", "天气之子", "铃芽之旅"]
    DAYS = 2
    try:
        print("🚀 开始生成路线...")
        locations = get_simulated_anime_locations()
        print(f"✅ 加载 {len(locations)} 个圣地")
        
        route_info = plan_optimal_route(locations)
        print(f"✅ 路线完成：{route_info['total_distance']}公里")
        
        itinerary = generate_itinerary_with_ollama(ANIME_NAMES, DAYS, locations, route_info)
        
        with open("动漫圣地巡礼路线规划.md", "w", encoding="utf-8") as f:
            f.write(itinerary)
        
        print("\n🎉 完成！已保存为 md 文件")
        print(itinerary)
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()