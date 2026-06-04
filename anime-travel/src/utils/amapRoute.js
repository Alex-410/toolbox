let AMap = window.AMap

let drivingPlugin = null
let walkingPlugin = null

function getAMap() {
  if (!AMap && window.AMap) {
    AMap = window.AMap
  }
  return AMap
}

function getDrivingPlugin() {
  return new Promise((resolve, reject) => {
    if (drivingPlugin) {
      resolve(drivingPlugin)
      return
    }

    const amap = getAMap()
    if (!amap) {
      reject(new Error('高德地图未加载'))
      return
    }

    amap.plugin(['AMap.Driving'], () => {
      drivingPlugin = new amap.Driving({
        policy: amap.DrivingPolicy.LEAST_TIME,
        city: '010',
        province: '京',
        citycode: '010',
        showMarker: false,
        autoFitView: false
      })
      resolve(drivingPlugin)
    })
  })
}

function getWalkingPlugin() {
  return new Promise((resolve, reject) => {
    if (walkingPlugin) {
      resolve(walkingPlugin)
      return
    }

    const amap = getAMap()
    if (!amap) {
      reject(new Error('高德地图未加载'))
      return
    }

    amap.plugin(['AMap.Walking'], () => {
      walkingPlugin = new amap.Walking({
        showMarker: false,
        autoFitView: false
      })
      resolve(walkingPlugin)
    })
  })
}

export function planDrivingRoute(origin, destination) {
  return new Promise((resolve, reject) => {
    if (!origin || !destination) {
      reject(new Error('起点或终点不能为空'))
      return
    }

    getDrivingPlugin().then((driving) => {
      driving.search(origin, destination, function (status, result) {
        if (status === 'complete' && result.routes && result.routes.length > 0) {
          const route = result.routes[0]
          const path = []

          if (route.steps) {
            route.steps.forEach(function (step) {
              if (step.path && step.path.length > 0) {
                path.push.apply(path, step.path)
              }
            })
          }

          resolve(path)
        } else {
          const errorMsg = result && result.info ? result.info : '驾车路线规划失败'
          reject(new Error(errorMsg))
        }
      })
    }).catch(function (error) {
      reject(error)
    })
  })
}

export function planWalkingRoute(origin, destination) {
  return new Promise((resolve, reject) => {
    if (!origin || !destination) {
      reject(new Error('起点或终点不能为空'))
      return
    }

    getWalkingPlugin().then((walking) => {
      walking.search(origin, destination, function (status, result) {
        if (status === 'complete' && result.routes && result.routes.length > 0) {
          const route = result.routes[0]
          const path = []

          if (route.steps) {
            route.steps.forEach(function (step) {
              if (step.path && step.path.length > 0) {
                path.push.apply(path, step.path)
              }
            })
          }

          resolve(path)
        } else {
          const errorMsg = result && result.info ? result.info : '步行路线规划失败'
          reject(new Error(errorMsg))
        }
      })
    }).catch(function (error) {
      reject(error)
    })
  })
}

export function batchPlanRoutes(points, type) {
  type = type || 'driving'
  const routes = []

  for (let i = 0; i < points.length - 1; i++) {
    const from = points[i]
    const to = points[i + 1]

    if (!from.geo || !to.geo) {
      routes.push({
        from: from.name,
        to: to.name,
        path: [[from.geo[1], from.geo[0]], [to.geo[1], to.geo[0]]],
        distance: 0,
        time: 0,
        isStraightLine: true
      })
      continue
    }

    const origin = [from.geo[1], from.geo[0]]
    const destination = [to.geo[1], to.geo[0]]

    const path = type === 'driving'
      ? [origin, destination]
      : [origin, destination]

    const distance = calculateDistance(path)
    const time = estimateTime(distance, type)

    routes.push({
      from: from.name,
      to: to.name,
      path: path,
      distance: distance,
      time: time,
      isStraightLine: true
    })
  }

  return routes
}

function calculateDistance(path) {
  if (!path || path.length < 2) return 0

  const amap = getAMap()
  if (!amap || !amap.GeometryUtil) {
    return 0
  }

  let totalDistance = 0

  for (let i = 0; i < path.length - 1; i++) {
    totalDistance += amap.GeometryUtil.distance(
      [path[i].lng, path[i].lat],
      [path[i + 1].lng, path[i + 1].lat]
    )
  }

  return Math.round(totalDistance)
}

function estimateTime(distanceMeters, type) {
  const speedKmH = type === 'driving' ? 40 : 5
  const distanceKm = distanceMeters / 1000
  const hours = distanceKm / speedKmH
  const minutes = Math.round(hours * 60)
  return minutes
}
