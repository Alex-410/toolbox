import axios from 'axios'

const api = axios.create({
  timeout: 15000,
  headers: {
    'Accept': 'application/json'
  }
})

api.interceptors.request.use((config) => {
  config.proxy = false
  return config
})

function handleError(error, subjectID) {
  if (error.response) {
    const status = error.response.status
    if (status === 404) {
      throw new Error(`未找到 ID 为 ${subjectID} 的作品巡礼数据，请确认 Bangumi ID 是否正确`)
    }
    if (status === 429) {
      throw new Error('请求过于频繁，请稍后再试')
    }
    throw new Error(`服务器返回错误 (${status})`)
  }
  if (error.code === 'ECONNABORTED') {
    throw new Error('请求超时，请检查网络连接后重试')
  }
  throw new Error('网络请求失败，请检查网络连接')
}

export async function fetchBangumiLite(subjectID) {
  try {
    const url = `/api/anitabi/bangumi/${subjectID}/lite`
    const response = await api.get(url)
    return response.data
  } catch (error) {
    handleError(error, subjectID)
  }
}

export async function fetchBangumiPointsDetail(subjectID, haveImage = false) {
  try {
    let url = `/api/anitabi/bangumi/${subjectID}/points/detail`
    if (haveImage) {
      url += '?haveImage=true'
    }
    const response = await api.get(url)
    return response.data
  } catch (error) {
    handleError(error, subjectID)
  }
}

export async function searchBangumiByKey(keyword) {
  try {
    const encoded = encodeURIComponent(keyword)
    const url = `/api/bgm/search/subject/${encoded}?type=2&responseGroup=small&max_results=10`
    const response = await api.get(url)
    if (!response.data || !response.data.list) return []
    return response.data.list.map(item => ({
      id: item.id,
      name: item.name,
      name_cn: item.name_cn || '',
      image: item.images ? (item.images.medium || item.images.common || '') : '',
      air_date: item.air_date || '',
      summary: item.summary || ''
    }))
  } catch (error) {
    if (error.response && error.response.status === 404) return []
    throw new Error('搜索作品失败，请稍后重试')
  }
}
