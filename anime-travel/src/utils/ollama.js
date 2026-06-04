import axios from 'axios'

const OLLAMA_BASE_URL = 'http://localhost:11434'
const OLLAMA_MODEL = 'deepseek-r1:1.5b'

const api = axios.create({
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export async function generateItineraryWithOllama(animeNames, days, locations, routeInfo) {
  const locationsJson = JSON.stringify(locations, null, 2)

  const prompt = `你是专业动漫圣地巡礼规划师，严格按照格式输出，不许改动结构！

【基本信息】
- 涉及作品：${animeNames.join(', ')}
- 旅行天数：${days}天
- 总地标：${locations.length}个
- 总距离：${routeInfo.totalDistance}公里
- 总时间：${routeInfo.totalDuration}分钟

【地标数据】
${locationsJson}

【输出格式（严格照搬）】
#多作品混合圣地巡礼路线规划（${days}日版）
## 整体规划说明
- 覆盖地标总数：${locations.length}个
- 涉及作品：${animeNames.map(n => `《${n}》`).join(', ')}
- 推荐出行方式：JR/地铁+步行
- 核心覆盖区域：东京都
- 推荐交通卡：Suica卡/东京地铁72小时券

---

## 第1天：区域巡礼
### 路线顺序：起点 → 地标1 → 地标2 → 地标3
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

## 第2天：区域巡礼
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
3. 分${days}天规划，每天3-4个地点
4. 打卡建议贴合动画场景`

  const payload = {
    model: OLLAMA_MODEL,
    messages: [
      { role: 'system', content: '你是严格遵守格式的规划师，只输出规划内容，无多余文字' },
      { role: 'user', content: prompt }
    ],
    stream: false
  }

  const response = await api.post(`${OLLAMA_BASE_URL}/api/chat`, payload)
  const result = response.data

  if (!result.message || !result.message.content) {
    throw new Error('Ollama API 错误: ' + JSON.stringify(result))
  }

  return result.message.content
}

export function checkOllamaStatus() {
  return api.get(`${OLLAMA_BASE_URL}/api/tags`)
    .then(function(response) {
      return {
        available: true,
        models: response.data.models || []
      }
    })
    .catch(function() {
      return {
        available: false,
        models: []
      }
    })
}
