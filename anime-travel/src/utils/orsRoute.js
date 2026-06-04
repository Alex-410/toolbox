import axios from 'axios'

const OPENROUTESERVICE_KEY = 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6Ijc5ZmJhMDk2N2NjNDQ3ZDE4ODQzYzc2NmZkNGU3N2FhIiwiaCI6Im11cm11cjY0In0='
const PROXY = {
  http: 'http://127.0.0.1:7892',
  https: 'http://127.0.0.1:7892'
}

const api = axios.create({
  timeout: 30000
})

function planRoute(origin, destination, mode) {
  return new Promise(function(resolve, reject) {
    if (!origin || !destination) {
      reject(new Error('起点或终点不能为空'))
      return
    }

    var url = 'https://api.openrouteservice.org/v2/directions/' + mode
    var data = {
      coordinates: [
        [origin[0], origin[1]],
        [destination[0], destination[1]]
      ]
    }
    var headers = {
      'Authorization': OPENROUTESERVICE_KEY,
      'Content-Type': 'application/json'
    }

    api.post(url, data, { 
      headers: headers,
      proxy: PROXY
    })
      .then(function(response) {
        if (response.data && response.data.routes && response.data.routes.length > 0) {
          var route = response.data.routes[0]
          var path = []

          if (route.geometry && route.geometry.coordinates) {
            path = route.geometry.coordinates.map(function(coord) {
              return { lng: coord[0], lat: coord[1] }
            })
          }

          resolve(path)
        } else {
          reject(new Error(mode + ' 路线规划失败: 无返回路线'))
        }
      })
      .catch(function(error) {
        var errorMsg = mode + ' 路线规划失败'
        if (error.response && error.response.data && error.response.data.error) {
          errorMsg += ': ' + error.response.data.error.message
        } else if (error.message) {
          errorMsg += ': ' + error.message
        }
        console.error('ORS ' + mode + ' 路线规划失败:', error.response ? error.response.data : error)
        reject(new Error(errorMsg))
      })
  })
}

export function planDrivingRoute(origin, destination) {
  return planRoute(origin, destination, 'driving-car')
}

export function planWalkingRoute(origin, destination) {
  return planRoute(origin, destination, 'foot-walking')
}

export function planCyclingRoute(origin, destination) {
  return planRoute(origin, destination, 'cycling-regular')
}

export function batchPlanRoutes(points, type) {
  type = type || 'driving'
  var routes = []

  for (var i = 0; i < points.length - 1; i++) {
    var from = points[i]
    var to = points[i + 1]

    if (!from.geo || !to.geo) {
      routes.push({
        from: from.name,
        to: to.name,
        path: [
          { lng: from.geo[1], lat: from.geo[0] },
          { lng: to.geo[1], lat: to.geo[0] }
        ],
        distance: 0,
        time: 0,
        isStraightLine: true
      })
      continue
    }

    var origin = [from.geo[1], from.geo[0]]
    var destination = [to.geo[1], to.geo[0]]

    routes.push({
      from: from.name,
      to: to.name,
      path: [
        { lng: origin[0], lat: origin[1] },
        { lng: destination[0], lat: destination[1] }
      ],
      distance: 0,
      time: 0,
      isStraightLine: true
    })
  }

  return routes
}
