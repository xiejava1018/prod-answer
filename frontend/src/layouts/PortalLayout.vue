<template>
  <div class="portal-layout">
    <!-- 导航栏 -->
    <header class="portal-header">
      <div class="container">
        <div class="header-content">
          <!-- Logo -->
          <div class="logo">
            <router-link to="/portal">
              <img src="/logo.png" alt="产品门户" />
              <span>产品门户</span>
            </router-link>
          </div>

          <!-- 导航菜单 -->
          <nav class="nav-menu">
            <router-link 
              v-for="item in navItems" 
              :key="item.path"
              :to="item.path"
              class="nav-item"
              :class="{ active: isActive(item.path) }"
            >
              {{ item.name }}
            </router-link>
          </nav>

          <!-- 右侧操作区 -->
          <div class="header-actions">
            <el-button 
              type="primary" 
              class="quick-match-btn"
              @click="goToMatching"
            >
              快速匹配
            </el-button>
            <router-link to="/dashboard" class="admin-link">
              管理后台
            </router-link>
          </div>
        </div>
      </div>
    </header>

    <!-- 主要内容区 -->
    <main class="portal-main">
      <router-view />
    </main>

    <!-- 页脚 -->
    <footer class="portal-footer">
      <div class="container">
        <div class="footer-content">
          <div class="footer-section">
            <h4>产品中心</h4>
            <ul>
              <li><router-link to="/portal/products">产品列表</router-link></li>
              <li><router-link to="/portal/compare">产品对比</router-link></li>
              <li><router-link to="/portal/matching">智能匹配</router-link></li>
            </ul>
          </div>
          <div class="footer-section">
            <h4>解决方案</h4>
            <ul>
              <li><router-link to="/portal/solutions">行业方案</router-link></li>
              <li><router-link to="/portal/resources">资源中心</router-link></li>
            </ul>
          </div>
          <div class="footer-section">
            <h4>关于我们</h4>
            <ul>
              <li><router-link to="/portal/about">公司简介</router-link></li>
              <li><router-link to="/portal/about">联系我们</router-link></li>
            </ul>
          </div>
          <div class="footer-section">
            <h4>联系方式</h4>
            <ul>
              <li>电话: 400-123-4567</li>
              <li>邮箱: contact@example.com</li>
              <li>地址: 北京市朝阳区xxx大厦</li>
            </ul>
          </div>
        </div>
        <div class="footer-bottom">
          <p>&copy; 2026 产品能力匹配系统. All rights reserved.</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const navItems = [
  { name: '首页', path: '/portal' },
  { name: '产品中心', path: '/portal/products' },
  { name: '解决方案', path: '/portal/solutions' },
  { name: '资源中心', path: '/portal/resources' },
  { name: '关于我们', path: '/portal/about' }
]

const isActive = (path: string) => {
  return route.path === path || route.path.startsWith(path + '/')
}

const goToMatching = () => {
  router.push('/portal/matching')
}
</script>

<style scoped lang="scss">
.portal-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f7fa;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.portal-header {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 1000;

  .header-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 64px;
  }

  .logo {
    a {
      display: flex;
      align-items: center;
      text-decoration: none;
      color: #303133;
      font-size: 20px;
      font-weight: 600;

      img {
        height: 32px;
        margin-right: 12px;
      }

      span {
        background: linear-gradient(135deg, #1890ff 0%, #722ed1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
      }
    }
  }

  .nav-menu {
    display: flex;
    gap: 32px;

    .nav-item {
      text-decoration: none;
      color: #606266;
      font-size: 16px;
      font-weight: 500;
      transition: all 0.3s;
      position: relative;

      &:hover {
        color: #1890ff;
      }

      &.active {
        color: #1890ff;

        &::after {
          content: '';
          position: absolute;
          bottom: -20px;
          left: 0;
          right: 0;
          height: 3px;
          background: #1890ff;
          border-radius: 2px;
        }
      }
    }
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 16px;

    .quick-match-btn {
      font-weight: 500;
    }

    .admin-link {
      text-decoration: none;
      color: #909399;
      font-size: 14px;

      &:hover {
        color: #1890ff;
      }
    }
  }
}

.portal-main {
  flex: 1;
  padding: 0;
}

.portal-footer {
  background: #303133;
  color: #fff;
  padding: 40px 0 20px;
  margin-top: auto;

  .footer-content {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 40px;
    margin-bottom: 30px;

    .footer-section {
      h4 {
        font-size: 16px;
        margin-bottom: 16px;
        color: #fff;
      }

      ul {
        list-style: none;
        padding: 0;
        margin: 0;

        li {
          margin-bottom: 8px;

          a {
            color: #e4e7ed;
            text-decoration: none;
            font-size: 14px;
            transition: color 0.3s;

            &:hover {
              color: #1890ff;
            }
          }
        }
      }
    }
  }

  .footer-bottom {
    border-top: 1px solid #4c4d4f;
    padding-top: 20px;
    text-align: center;

    p {
      margin: 0;
      font-size: 14px;
      color: #a8abb2;
    }
  }
}

@media (max-width: 768px) {
  .portal-header {
    .header-content {
      flex-wrap: wrap;
      height: auto;
      padding: 12px 0;
    }

    .nav-menu {
      display: none;
    }

    .header-actions {
      .admin-link {
        display: none;
      }
    }
  }

  .portal-footer {
    .footer-content {
      grid-template-columns: repeat(2, 1fr);
      gap: 24px;
    }
  }
}
</style>