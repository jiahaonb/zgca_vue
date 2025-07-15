<template>
  <div id="app">
    <el-container>
      <!-- 顶部导航栏 -->
      <el-header class="header">
        <div class="header-content">
          <div class="logo">
            <el-icon><DataLine /></el-icon>
            <span class="title">ZGCA多智能体剧本编辑系统</span>
          </div>
          <el-menu
            mode="horizontal"
            :default-active="$route.path"
            class="nav-menu"
            router
          >
            <el-menu-item index="/script">
              <el-icon><Edit /></el-icon>
              <span>创建剧本</span>
            </el-menu-item>
            <el-menu-item index="/chat">
              <el-icon><ChatDotRound /></el-icon>
              <span>剧本对话</span>
            </el-menu-item>
            <el-menu-item index="/status">
              <el-icon><Monitor /></el-icon>
              <span>系统状态</span>
            </el-menu-item>
          </el-menu>
          <div class="status-indicator">
            <el-badge :value="connectionStatus ? '在线' : '离线'" :type="connectionStatus ? 'success' : 'danger'" is-dot>
              <el-icon><Connection /></el-icon>
            </el-badge>
          </div>
        </div>
      </el-header>

      <!-- 主体内容区域 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>

    <!-- 全局加载提示 -->
    <el-dialog v-model="loadingVisible" title="系统提示" width="30%" :show-close="false" center>
      <div class="loading-content">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <p>{{ loadingMessage }}</p>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, provide } from 'vue'
import apiService from './services/api.js'

export default {
  name: 'App',
  setup() {
    const connectionStatus = ref(false)
    const loadingVisible = ref(false)
    const loadingMessage = ref('正在加载...')

    // 提供全局加载方法
    const showLoading = (message = '正在加载...') => {
      loadingMessage.value = message
      loadingVisible.value = true
    }

    const hideLoading = () => {
      loadingVisible.value = false
    }

    // 检查系统连接状态
    const checkConnection = async () => {
      try {
        await apiService.getStatus()
        connectionStatus.value = true
      } catch (error) {
        connectionStatus.value = false
        console.error('连接状态检查失败:', error)
      }
    }

    // 定期检查连接状态
    const startConnectionCheck = () => {
      checkConnection()
      setInterval(checkConnection, 10000) // 每10秒检查一次
    }

    // 提供给子组件使用
    provide('showLoading', showLoading)
    provide('hideLoading', hideLoading)
    provide('checkConnection', checkConnection)

    onMounted(() => {
      startConnectionCheck()
    })

    return {
      connectionStatus,
      loadingVisible,
      loadingMessage,
      showLoading,
      hideLoading
    }
  }
}
</script>

<style scoped>
#app {
  height: 100vh;
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 0;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 20px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: bold;
}

.title {
  background: linear-gradient(45deg, #ffffff, #e8f4f8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-menu {
  flex: 1;
  margin: 0 20px;
  background: transparent;
  border-bottom: none;
}

.nav-menu .el-menu-item {
  color: rgba(255, 255, 255, 0.8);
  border-bottom: 2px solid transparent;
  transition: all 0.3s ease;
}

.nav-menu .el-menu-item:hover,
.nav-menu .el-menu-item.is-active {
  color: white;
  background: rgba(255, 255, 255, 0.1);
  border-bottom-color: white;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.main-content {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.loading-content {
  text-align: center;
  padding: 20px;
}

.loading-icon {
  font-size: 24px;
  color: #409EFF;
  margin-bottom: 10px;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    padding: 10px;
  }
  
  .nav-menu {
    margin: 10px 0;
  }
  
  .title {
    font-size: 16px;
  }
}
</style>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif;
  background: #f5f7fa;
}

.el-container {
  height: 100vh;
}

/* Element Plus 样式覆盖 */
.el-menu--horizontal > .el-menu-item {
  height: 60px;
  line-height: 60px;
}

.el-header {
  height: 60px !important;
  line-height: 60px;
}

.el-main {
  padding: 20px;
}
</style> 