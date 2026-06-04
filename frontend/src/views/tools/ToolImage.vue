<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>腾讯地图终极修复测试</title>
  <style>
    body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
    #map { width: 100%; height: 700px; border: 1px solid #eee; }
    .controls { padding: 10px; background: #f5f5f5; }
    button { margin: 0 5px; padding: 6px 12px; cursor: pointer; }
    #log { background: #222; color: #0f0; padding: 10px; margin-top: 10px; font-family: monospace; max-height: 200px; overflow-y: auto; }
  </style>
</head>
<body>
  <div class="controls">
    <button onclick="searchNearby()">搜索附近酒店</button>
    <button onclick="drawRoute()">绘制上海→迪士尼路线</button>
  </div>

  <div id="map"></div>
  <div id="log">加载中...</div>

  <script>
    const TENCENT_KEY = "YUKBZ-JIPCU-5DSVO-G2QGP-O7ONO-IHBAR";
    let map = null;
    let qqMaps = null;
    const logEl = document.getElementById('log');

    function log(msg) {
      logEl.innerHTML += `<br>[${new Date().toLocaleTimeString()}] ${msg}`;
      logEl.scrollTop = logEl.scrollHeight;
    }

    // 关键修复：使用回调方式加载地图API，避免qq.maps对象未初始化
    window.initTencentMap = function() {
      qqMaps = window.qq.maps;
      log("✅ JS API加载成功，qq.maps对象已就绪");
      initMap();
    };

    // 1. 加载腾讯地图JS API（用官方推荐的回调方式）
    function loadMapAPI() {
      log("正在加载腾讯地图JS API...");
      const script = document.createElement('script');
      // 官方推荐的回调方式：onload=initTencentMap
      script.src = `https://map.qq.com/api/js?v=2.exp&key=${TENCENT_KEY}&callback=initTencentMap`;
      script.onerror = () => log("❌ JS API加载失败，请检查网络或Key");
      document.body.appendChild(script);
    }

    // 2. 初始化地图（确保qqMaps已就绪）
    function initMap() {
      try {
        log("正在初始化地图...");
        map = new qqMaps.Map(document.getElementById('map'), {
          center: new qqMaps.LatLng(31.230416, 121.473701),
          zoom: 12
        });
        log("✅ 地图初始化成功！");

        // 添加标记点
        new qqMaps.Marker({
          position: new qqMaps.LatLng(31.230416, 121.473701),
          map: map
        });

      } catch (err) {
        log(`❌ 地图初始化错误：${err.message}`);
        console.error(err);
      }
    }

    // 3. 地点搜索（使用JSONP解决跨域）
    function searchNearby() {
      try {
        log("正在调用地点搜索API...");
        // 用JSONP方式请求，避免fetch跨域
        const callbackName = 'searchNearbyCallback';
        window[callbackName] = function(data) {
          if (data.status === 0) {
            log(`✅ 地点搜索成功，共找到${data.count}个结果`);
            // 添加标记
            data.data.forEach(item => {
              new qqMaps.Marker({
                position: new qqMaps.LatLng(item.location.lat, item.location.lng),
                map: map,
                title: item.title
              });
            });
          } else {
            log(`⚠️ 地点搜索失败：${data.message}`);
          }
          delete window[callbackName];
        };

        const script = document.createElement('script');
        script.src = `https://apis.map.qq.com/ws/place/v1/search?keyword=酒店&boundary=nearby(39.908491,116.374328,1000)&key=${TENCENT_KEY}&callback=${callbackName}`;
        script.onerror = () => log("❌ 地点搜索请求失败");
        document.body.appendChild(script);
      } catch (err) {
        log(`❌ 地点搜索错误：${err.message}`);
      }
    }

    // 4. 路线规划（同样用JSONP解决跨域）
    function drawRoute() {
      try {
        log("正在调用路线规划API...");
        const callbackName = 'drawRouteCallback';
        window[callbackName] = function(data) {
          if (data.status === 0) {
            log("✅ 路线规划成功，正在绘制路线...");
            const polylineStr = data.result.routes[0].polyline;
            const path = [];
            for (let i = 0; i < polylineStr.length; i += 2) {
              path.push(new qqMaps.LatLng(polylineStr[i + 1], polylineStr[i]));
            }

            new qqMaps.Polyline({
              path: path,
              strokeColor: "#2E8B57",
              strokeWeight: 6,
              map: map
            });

            map.fitBounds(new qqMaps.LatLngBounds(path));
          } else {
            log(`⚠️ 路线规划失败：${data.message}`);
          }
          delete window[callbackName];
        };

        const script = document.createElement('script');
        script.src = `https://apis.map.qq.com/ws/direction/v1/driving/?from=121.475078,31.235929&to=121.68898,31.14434&key=${TENCENT_KEY}&callback=${callbackName}`;
        script.onerror = () => log("❌ 路线规划请求失败");
        document.body.appendChild(script);
      } catch (err) {
        log(`❌ 路线规划错误：${err.message}`);
      }
    }

    // 页面加载后启动
    window.onload = loadMapAPI;
  </script>
</body>
</html>