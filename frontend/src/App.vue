<template>
  <el-container class="app-container">
    <!-- Header -->
    <el-header class="app-header">
      <div class="header-left">
        <h1 class="logo">产品能力匹配系统</h1>
      </div>
      <div class="header-right">
        <el-menu
          :default-active="activeMenu"
          mode="horizontal"
          :ellipsis="false"
          router
          class="header-menu"
        >
          <el-menu-item index="/dashboard">仪表盘</el-menu-item>
          <el-menu-item index="/products">产品管理</el-menu-item>
          <el-menu-item index="/requirements">需求管理</el-menu-item>
          <el-menu-item index="/matching">匹配分析</el-menu-item>
          <el-menu-item index="/settings/embeddings">系统设置</el-menu-item>
        </el-menu>
      </div>
    </el-header>

    <!-- Main Content -->
    <el-main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const activeMenu = computed(() => {
  return route.path
})
</script>

<style scoped lang="scss">
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background-color: #fff;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px !important;

  .header-left {
    .logo {
      font-size: 20px;
      font-weight: 600;
      color: var(--primary-color);
      margin: 0;
    }
  }

  .header-right {
    flex: 1;
    display: flex;
    justify-content: flex-end;

    .header-menu {
      border-bottom: none;
    }
  }
}

.app-main {
  background-color: var(--bg-color);
  padding: 20px;
  overflow-y: auto;
}

// Fade transition
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
