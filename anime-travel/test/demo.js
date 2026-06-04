import ollama from 'ollama';
import fetch from 'node-fetch';
import { HttpsProxyAgent } from 'https-proxy-agent';

// ====================== 配置区（已填好你的Key和代理） ======================
const OPENROUTESERVICE_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6Ijc5ZmJhMDk2N2NjNDQ3ZDE4ODQzYzc2NmZkNGU3N2FhIiwiaCI6Im11cm11cjY0In0=";
const PROXY_URL = "http://127.0.0.1:7892"; // 已改成你的端口
// ===========================================================================

// 创建带代理的 fetch
const agent = new HttpsProxyAgent(PROXY_URL);
const proxiedFetch = (url, options = {}) => fetch(url, { ...options, agent });

// 1. 地名转坐标（Nominatim，通过代理访问）
async function getCoordinates(address) {
  console.log(`📍 正在解析地址：${address}`);
  const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(address)}&format=json&limit=1&countrycodes=jp`;
  const res = await proxiedFetch(url, { 
    headers: { 'User-Agent': 'JapanTravelPlanner/1.0' } 
  });
  const data = await res.json();
  if (data.length === 0) throw new Error(`无法解析地址：${address}`);
  return { lat: parseFloat(data[0].lat), lon: parseFloat(data[0].lon) };
}

// 2. 日本路线规划（OpenRouteService，通过代理访问）
async function getRoute(origin, destination, mode = 'foot-walking') {
  console.log(`🗺️ 正在规划路线：${origin} → ${destination}`);
  const [start, end] = await Promise.all([getCoordinates(origin), getCoordinates(destination)]);
  
  const url = `https://api.openrouteservice.org/v2/directions/${mode}`;
  const res = await proxiedFetch(url, {
    method: 'POST',
    headers: {
      'Authorization': OPENROUTESERVICE_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      coordinates: [[start.lon, start.lat], [end.lon, end.lat]],
      language: 'zh-CN',
      instructions: true
    })
  });
  
  const data = await res.json();
  if (data.error) throw new Error(`路线规划失败：${data.error.message}`);
  
  const route = data.routes[0];
  return {
    distance: (route.summary.distance / 1000).toFixed(1) + '公里',
    duration: Math.round(route.summary.duration / 60) + '分钟',
    steps: route.segments[0].steps.map(s => s.instruction)
  };
}

// 3. 主逻辑
async function planJapanTravel(question) {
  console.log("🙍‍♂️ 用户问题：", question);
  
  const parseRes = await ollama.chat({
    model: "qwen3-vl:4b",
    messages: [
      {
        role: "system",
        content: `解析用户问题，提取起点(origin)和终点(destination)，只返回JSON。例如：{"origin":"东京站","destination":"浅草寺"}`
      },
      { role: "user", content: question }
    ],
    stream: false
  });
  
  let params;
  try {
    params = JSON.parse(parseRes.message.content);
  } catch (e) {
    console.error("❌ 问题解析失败，请明确说明起点和终点");
    return;
  }
  
  const routeInfo = await getRoute(params.origin, params.destination);
  
  const finalRes = await ollama.chat({
    model: "qwen3-vl:4b",
    messages: [
      {
        role: "system",
        content: `你是日本旅行规划师。请根据路线信息，用简洁友好的中文回答。必须完全基于提供的信息，不要编造。`
      },
      {
        role: "user",
        content: `用户问题：${question}\n\n路线信息：\n距离：${routeInfo.distance}\n预计时间：${routeInfo.duration}\n详细步骤：\n${routeInfo.steps.join('\n')}`
      }
    ],
    stream: false
  });
  
  console.log("\n🤖 最终规划：\n", finalRes.message.content);
}

// 测试
planJapanTravel("从东京站怎么去浅草寺？要步行路线。");