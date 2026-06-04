<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="sidebar-content">
        <SearchPanel />
        <CoordinateLibrary />
      </div>
    </aside>
    <main class="main-content">
      <MapView />
      <LandmarkDock />
    </main>
  </div>
</template>

<script setup>
import SearchPanel from './components/SearchPanel.vue'
import CoordinateLibrary from './components/CoordinateLibrary.vue'
import MapView from './components/MapView.vue'
import LandmarkDock from './components/LandmarkDock.vue'
</script>

<style scoped>
.app-layout {
  display: flex;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 360px;
  min-width: 360px;
  height: 100vh;
  background-color: var(--sidebar-bg);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.main-content {
  flex: 1;
  height: 100vh;
  overflow: hidden;
  position: relative;
}
</style>
