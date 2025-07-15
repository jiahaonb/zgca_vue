<template>
  <div class="system-status">
    <el-row :gutter="20">
      <!-- 系统状态卡片 -->
      <el-col :span="8">
        <el-card class="status-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Monitor /></el-icon>
              <span>系统状态</span>
              <el-button size="small" @click="refreshStatus" :loading="refreshing">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          
          <div class="status-content">
            <div class="status-item">
              <div class="status-label">连接状态</div>
              <el-tag :type="systemStatus.connected ? 'success' : 'danger'">
                {{ systemStatus.connected ? '已连接' : '断开连接' }}
              </el-tag>
            </div>
            
            <div class="status-item">
              <div class="status-label">后端服务</div>
              <el-tag :type="systemStatus.bridge_status === 'running' ? 'success' : 'warning'">
                {{ systemStatus.bridge_status || '未知' }}
              </el-tag>
            </div>
            
            <div class="status-item">
              <div class="status-label">剧本系统</div>
              <el-tag :type="systemStatus.script_system_available ? 'success' : 'info'">
                {{ systemStatus.script_system_available ? '可用' : '不可用' }}
              </el-tag>
            </div>
            
            <div class="status-item">
              <div class="status-label">服务端口</div>
              <span class="status-value">{{ systemStatus.port || '8900' }}</span>
            </div>
            
            <div class="status-item">
              <div class="status-label">运行时间</div>
              <span class="status-value">{{ uptime }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 剧本信息卡片 -->
      <el-col :span="8">
        <el-card class="script-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>剧本信息</span>
            </div>
          </template>
          
          <div class="script-content">
            <div v-if="!systemStatus.initialized" class="no-script">
              <el-empty description="暂无剧本" :image-size="80">
                <el-button type="primary" @click="goToScript">创建剧本</el-button>
              </el-empty>
            </div>
            
            <div v-else class="script-info">
              <div class="info-item">
                <div class="info-label">初始化状态</div>
                <el-tag type="success">已初始化</el-tag>
              </div>
              
              <div class="info-item">
                <div class="info-label">角色总数</div>
                <span class="info-value">{{ systemStatus.characters_count || 0 }} 个</span>
              </div>
              
              <div class="info-item">
                <div class="info-label">对话轮数</div>
                <span class="info-value">{{ systemStatus.conversation_count || 0 }} 轮</span>
              </div>
              
              <div v-if="characters.length > 0" class="characters-section">
                <div class="info-label">角色列表</div>
                <div class="characters-grid">
                  <div 
                    v-for="character in characters" 
                    :key="character.name"
                    class="character-badge"
                  >
                    <span class="character-icon">
                      {{ character.type === 'user' ? '👤' : '🤖' }}
                    </span>
                    <span class="character-name">{{ character.name }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- API状态卡片 -->
      <el-col :span="8">
        <el-card class="api-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Connection /></el-icon>
              <span>API状态</span>
            </div>
          </template>
          
          <div class="api-content">
            <div class="api-item">
              <div class="api-label">可用密钥</div>
              <div class="api-progress">
                <el-progress 
                  :percentage="apiUsagePercentage" 
                  :color="getProgressColor(apiUsagePercentage)"
                  :show-text="false"
                />
                <span class="progress-text">
                  {{ systemStatus.api_pool_available || 0 }} / {{ systemStatus.api_pool_total || 0 }}
                </span>
              </div>
            </div>
            
            <div class="api-item">
              <div class="api-label">响应时间</div>
              <span class="api-value">{{ responseTime }}ms</span>
            </div>
            
            <div class="api-item">
              <div class="api-label">请求状态</div>
              <el-tag :type="lastRequestStatus === 'success' ? 'success' : 'danger'">
                {{ lastRequestStatus === 'success' ? '正常' : '异常' }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统详细信息 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card class="details-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><DataLine /></el-icon>
              <span>系统日志</span>
              <el-button size="small" @click="clearLogs">清空日志</el-button>
            </div>
          </template>
          
          <div class="logs-content">
            <div v-if="systemLogs.length === 0" class="no-logs">
              <el-text type="info">暂无系统日志</el-text>
            </div>
            <div v-else class="logs-list">
              <div 
                v-for="(log, index) in systemLogs" 
                :key="index"
                class="log-item"
                :class="log.type"
              >
                <span class="log-time">{{ formatTime(log.time) }}</span>
                <span class="log-message">{{ log.message }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="actions-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Tools /></el-icon>
              <span>系统操作</span>
            </div>
          </template>
          
          <div class="actions-content">
            <div class="action-group">
              <h4>剧本管理</h4>
              <div class="action-buttons">
                <el-button type="primary" @click="goToScript">
                  <el-icon><Edit /></el-icon>
                  创建剧本
                </el-button>
                <el-button type="success" @click="goToChat">
                  <el-icon><ChatDotRound /></el-icon>
                  开始对话
                </el-button>
                <el-button type="danger" @click="clearHistory">
                  <el-icon><Delete /></el-icon>
                  清空历史
                </el-button>
              </div>
            </div>
            
            <div class="action-group">
              <h4>系统管理</h4>
              <div class="action-buttons">
                <el-button type="info" @click="testConnection">
                  <el-icon><Link /></el-icon>
                  测试连接
                </el-button>
                <el-button type="warning" @click="exportLogs">
                  <el-icon><Download /></el-icon>
                  导出日志
                </el-button>
                <el-button @click="refreshAll">
                  <el-icon><Refresh /></el-icon>
                  全部刷新
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, inject } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import apiService from '../services/api.js'

export default {
  name: 'SystemStatus',
  setup() {
    const router = useRouter()
    const checkConnection = inject('checkConnection')

    const refreshing = ref(false)
    const systemStatus = ref({
      connected: false,
      bridge_status: '',
      script_system_available: false,
      port: 8900,
      initialized: false,
      characters_count: 0,
      conversation_count: 0,
      api_pool_available: 0,
      api_pool_total: 0
    })
    
    const characters = ref([])
    const systemLogs = ref([])
    const responseTime = ref(0)
    const lastRequestStatus = ref('success')
    const startTime = ref(Date.now())
    const currentTime = ref(Date.now())

    // 计算运行时间
    const uptime = computed(() => {
      const diff = currentTime.value - startTime.value
      const seconds = Math.floor(diff / 1000)
      const minutes = Math.floor(seconds / 60)
      const hours = Math.floor(minutes / 60)
      
      if (hours > 0) {
        return `${hours}小时${minutes % 60}分钟`
      } else if (minutes > 0) {
        return `${minutes}分钟${seconds % 60}秒`
      } else {
        return `${seconds}秒`
      }
    })

    // 计算API使用百分比
    const apiUsagePercentage = computed(() => {
      const total = systemStatus.value.api_pool_total || 1
      const available = systemStatus.value.api_pool_available || 0
      return Math.round((available / total) * 100)
    })

    // 获取进度条颜色
    const getProgressColor = (percentage) => {
      if (percentage > 60) return '#67c23a'
      if (percentage > 30) return '#e6a23c'
      return '#f56c6c'
    }

    // 添加系统日志
    const addLog = (message, type = 'info') => {
      systemLogs.value.unshift({
        time: new Date(),
        message,
        type
      })
      // 只保留最近50条日志
      if (systemLogs.value.length > 50) {
        systemLogs.value = systemLogs.value.slice(0, 50)
      }
    }

    // 格式化时间
    const formatTime = (date) => {
      return date.toLocaleTimeString('zh-CN', { hour12: false })
    }

    // 刷新系统状态
    const refreshStatus = async () => {
      refreshing.value = true
      const startTime = Date.now()
      
      try {
        // 获取系统状态
        const statusResult = await apiService.getStatus()
        responseTime.value = Date.now() - startTime
        
        if (statusResult.success) {
          systemStatus.value = { ...systemStatus.value, ...statusResult, connected: true }
          lastRequestStatus.value = 'success'
          addLog('系统状态刷新成功', 'success')
        }
        
        // 获取系统详细信息
        try {
          const infoResult = await apiService.getSystemInfo()
          if (infoResult.success) {
            systemStatus.value = { ...systemStatus.value, ...infoResult }
            if (infoResult.characters) {
              characters.value = infoResult.characters
            }
          }
        } catch (error) {
          console.error('获取详细信息失败:', error)
        }
        
      } catch (error) {
        systemStatus.value.connected = false
        lastRequestStatus.value = 'error'
        responseTime.value = Date.now() - startTime
        addLog(`连接失败: ${error.message}`, 'error')
        ElMessage.error('刷新状态失败')
      } finally {
        refreshing.value = false
      }
    }

    // 测试连接
    const testConnection = async () => {
      addLog('开始测试连接...', 'info')
      await refreshStatus()
      if (systemStatus.value.connected) {
        ElMessage.success('连接测试成功')
        addLog('连接测试成功', 'success')
      } else {
        ElMessage.error('连接测试失败')
        addLog('连接测试失败', 'error')
      }
    }

    // 清空历史
    const clearHistory = async () => {
      try {
        await ElMessageBox.confirm('确定要清空对话历史吗？', '确认操作', {
          type: 'warning'
        })
        
        await apiService.clearHistory()
        ElMessage.success('历史记录已清空')
        addLog('对话历史已清空', 'success')
        await refreshStatus()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('清空历史失败')
          addLog(`清空历史失败: ${error.message}`, 'error')
        }
      }
    }

    // 清空日志
    const clearLogs = () => {
      systemLogs.value = []
      ElMessage.success('日志已清空')
    }

    // 导出日志
    const exportLogs = () => {
      const logText = systemLogs.value
        .map(log => `[${formatTime(log.time)}] ${log.type.toUpperCase()}: ${log.message}`)
        .join('\n')
      
      const blob = new Blob([logText], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `system-logs-${new Date().toISOString().slice(0, 10)}.txt`
      a.click()
      URL.revokeObjectURL(url)
      
      ElMessage.success('日志导出成功')
      addLog('系统日志已导出', 'info')
    }

    // 全部刷新
    const refreshAll = async () => {
      addLog('开始全面刷新系统状态...', 'info')
      await refreshStatus()
      if (checkConnection) {
        await checkConnection()
      }
      ElMessage.success('全部刷新完成')
      addLog('系统状态全面刷新完成', 'success')
    }

    // 跳转到剧本创建
    const goToScript = () => {
      router.push('/script')
      addLog('导航到剧本创建页面', 'info')
    }

    // 跳转到对话界面
    const goToChat = () => {
      router.push('/chat')
      addLog('导航到对话界面', 'info')
    }

    // 定时器
    let statusTimer = null
    let timeTimer = null

    onMounted(async () => {
      addLog('系统状态页面已加载', 'info')
      await refreshStatus()
      
      // 定期刷新状态（每30秒）
      statusTimer = setInterval(refreshStatus, 30000)
      
      // 更新运行时间（每秒）
      timeTimer = setInterval(() => {
        currentTime.value = Date.now()
      }, 500)
    })

    onUnmounted(() => {
      if (statusTimer) clearInterval(statusTimer)
      if (timeTimer) clearInterval(timeTimer)
    })

    return {
      refreshing,
      systemStatus,
      characters,
      systemLogs,
      responseTime,
      lastRequestStatus,
      uptime,
      apiUsagePercentage,
      getProgressColor,
      formatTime,
      refreshStatus,
      testConnection,
      clearHistory,
      clearLogs,
      exportLogs,
      refreshAll,
      goToScript,
      goToChat
    }
  }
}
</script>

<style scoped>
.system-status {
  max-width: 1400px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: bold;
  font-size: 16px;
}

.card-header > div:first-child {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-content,
.script-content,
.api-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-item,
.info-item,
.api-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.status-item:last-child,
.info-item:last-child,
.api-item:last-child {
  border-bottom: none;
}

.status-label,
.info-label,
.api-label {
  font-weight: 500;
  color: #606266;
}

.status-value,
.info-value,
.api-value {
  font-weight: bold;
  color: #303133;
}

.no-script {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.characters-section {
  margin-top: 16px;
}

.characters-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.character-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: #f5f7fa;
  border-radius: 12px;
  font-size: 12px;
}

.character-icon {
  font-size: 14px;
}

.api-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  margin-left: 16px;
}

.progress-text {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}

.logs-content {
  max-height: 300px;
  overflow-y: auto;
}

.no-logs {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100px;
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.log-item {
  display: flex;
  gap: 12px;
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.4;
}

.log-item.success {
  background: #f0f9ff;
  color: #409eff;
}

.log-item.error {
  background: #fef0f0;
  color: #f56c6c;
}

.log-item.warning {
  background: #fdf6ec;
  color: #e6a23c;
}

.log-item.info {
  background: #f4f4f5;
  color: #909399;
}

.log-time {
  color: #909399;
  white-space: nowrap;
}

.actions-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.action-group h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 14px;
  font-weight: bold;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .system-status {
    padding: 0 10px;
  }
}

@media (max-width: 768px) {
  .el-col {
    margin-bottom: 20px;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .characters-grid {
    flex-direction: column;
  }
  
  .api-progress {
    flex-direction: column;
    align-items: stretch;
    gap: 4px;
  }
}
</style> 