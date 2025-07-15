<template>
  <div class="chat-interface">
    <el-row :gutter="20">
      <!-- 对话区域 -->
      <el-col :span="18">
                <el-card class="chat-card" shadow="hover">
          <template #header>
            <div class="chat-header">
              <div class="header-info">
                <el-icon><ChatDotRound /></el-icon>
                <span>剧本对话</span>
                <el-tag v-if="isScriptReady" type="success" size="small">剧本已就绪</el-tag>
                <el-tag v-else type="warning" size="small">请先创建剧本</el-tag>
              </div>
              <div class="header-actions">
                <el-button size="small" @click="loadHistory">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
                <el-button size="small" type="warning" @click="clearChat">
                  <el-icon><Delete /></el-icon>
                  清空历史
                </el-button>
                <el-button size="small" type="danger" @click="endScript">
                  <el-icon><Close /></el-icon>
                  结束剧本
                </el-button>
              </div>
            </div>
          </template>

          <div class="chat-container">
            <!-- 对话历史区域 -->
            <div class="chat-history" ref="chatHistoryRef">
              <!-- 剧本结束状态显示 -->
              <div v-if="scriptEnded && chatHistory.length === 0" class="script-ended-notice">
                <el-result icon="success" title="剧本已结束" sub-title="您可以创建新的剧本开始全新的故事">
                  <template #extra>
                    <el-button type="primary" @click="goToScript">
                      <el-icon><Edit /></el-icon>
                      创建新剧本
                    </el-button>
                  </template>
                </el-result>
              </div>

              <!-- 空状态显示 -->
              <div v-else-if="chatHistory.length === 0" class="empty-chat">
                <el-empty description="还没有对话记录">
                  <el-button v-if="!isScriptReady" type="primary" @click="goToScript">
                    创建剧本
                  </el-button>
                  <el-button v-else type="primary" @click="startChat">
                    开始对话
                  </el-button>
                </el-empty>
              </div>
              
              <div v-else class="messages-container">
                <!-- 对话开始提示 -->
                <div class="status-tip">
                  <span>🎭 对话已开始，第 {{ currentRound }} 轮</span>
                </div>

                <div 
                  v-for="(message, index) in chatHistory" 
                  :key="index"
                >
                  <!-- 系统消息显示为状态提示 -->
                  <div v-if="isSystemMessage(message)" class="status-tip system-message">
                    <span>🔄 {{ getMessageText(message) }}</span>
                  </div>
                  
                  <!-- 普通消息 -->
                  <div v-else>
                    <div 
                      class="message-item"
                      :class="{ 'user-message': isUserMessage(message), 'ai-message': !isUserMessage(message) }"
                    >
                      <div class="message-avatar">
                        <el-avatar :size="40">
                          {{ getMessageAvatar(message) }}
                        </el-avatar>
                      </div>
                      <div class="message-content">
                        <div class="message-header">
                          <span class="speaker-name">{{ getSpeakerName(message) }}</span>
                          <span class="message-time">{{ formatTime(new Date()) }}</span>
                        </div>
                        <div class="message-text">{{ getMessageText(message) }}</div>
                      </div>
                    </div>

                    <!-- 在用户消息后显示状态提示 -->
                    <div v-if="isUserMessage(message) && index === chatHistory.length - 1 && !isTyping" class="status-tip">
                      <span>⏳ 等待AI角色回复...</span>
                    </div>
                  </div>
                </div>

                <!-- 打字指示器 -->
                <div v-if="isTyping" class="typing-indicator">
                  <div class="typing-avatar">
                    <el-avatar :size="40">🤖</el-avatar>
                  </div>
                  <div class="typing-content">
                    <div class="typing-text">
                      <span>{{ typingSpeaker || 'AI' }}</span> 正在思考中
                      <span class="typing-dots">
                        <span>.</span><span>.</span><span>.</span>
                      </span>
                    </div>
                  </div>
                </div>

                <!-- 发送状态提示 -->
                <div v-if="isSending" class="status-tip">
                  <span>📤 正在发送消息...</span>
                </div>

                <!-- 下一步提示 -->
                <div v-else-if="chatHistory.length > 0 && !isTyping" class="status-tip next-action">
                  <span v-if="shouldUserSpeak && currentMessage.trim()">
                    ✍️ 继续输入或点击发送按钮
                  </span>
                  <span v-else-if="shouldUserSpeak">
                    💭 您是否需要在此处发言？如果需要，请在下方输入台词
                  </span>
                  <span v-else-if="nextSpeaker">
                    🎯 下一个发言者：{{ nextSpeaker }}
                  </span>
                  <span v-else>
                    🔄 请点击"调度下一个角色"或继续对话
                  </span>
                </div>

                <!-- 系统状态提示 -->
                <div v-if="!isScriptReady" class="status-tip warning">
                  <span>⚠️ 请先创建剧本才能开始对话</span>
                </div>
              </div>
            </div>

            <!-- 消息输入区域 -->
            <div class="message-input">
              <div class="input-wrapper">
                <el-input
                  v-model="currentMessage"
                  type="textarea"
                  :rows="3"
                  placeholder="输入您的台词..."
                  @keydown.ctrl.enter="sendMessage"
                  :disabled="!isScriptReady || isSending"
                  show-word-limit
                  maxlength="500"
                  resize="none"
                />
              </div>
              <div class="input-actions">
                <div class="input-tips">
                  <span class="tip-text">Ctrl + Enter 快速发送</span>
                  <span class="round-info">第 {{ currentRound }} 轮对话</span>
                </div>
                <div class="action-buttons">
                  <el-button 
                    type="default" 
                    @click="skipTurn"
                    :disabled="!isScriptReady || isSending"
                  >
                    {{ isSending ? '调度中...' : '跳过发言' }}
                  </el-button>
                  <el-button 
                    type="primary" 
                    @click="sendMessage"
                    :loading="isSending"
                    :disabled="!isScriptReady || !currentMessage.trim()"
                  >
                    {{ isSending ? '发送中...' : '发送' }}
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 侧边信息面板 -->
      <el-col :span="6">
        <el-card class="info-panel" shadow="hover">
          <template #header>
            <div class="panel-header">
              <el-icon><User /></el-icon>
              <span>对话信息</span>
            </div>
          </template>

          <!-- 角色信息 -->
          <div class="character-section">
            <h4>剧本角色</h4>
            <div v-if="characters.length === 0" class="no-characters">
              <el-text type="info">暂无角色信息</el-text>
            </div>
            <div v-else class="characters-list">
              <div 
                v-for="character in characters" 
                :key="character.name"
                class="character-item"
                :class="{ 'active-speaker': character.name === nextSpeaker }"
              >
                <div class="character-avatar">
                  {{ character.type === 'user' ? '👤' : '🤖' }}
                </div>
                <div class="character-info">
                  <div class="character-name">{{ character.name }}</div>
                  <div class="character-type">{{ character.type === 'user' ? '用户主角' : 'AI角色' }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 对话统计 -->
          <div class="stats-section">
            <h4>对话统计</h4>
            <el-descriptions :column="1" size="small">
              <el-descriptions-item label="当前轮次">{{ currentRound }}</el-descriptions-item>
              <el-descriptions-item label="总消息数">{{ chatHistory.length }}</el-descriptions-item>
              <el-descriptions-item label="下一个发言">{{ nextSpeaker || '待确定' }}</el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 快捷操作 -->
          <div class="actions-section">
            <h4>快捷操作</h4>
            <div class="action-list">
              <el-button size="small" type="primary" @click="autoConversation" :disabled="!isScriptReady">
                <el-icon><Magic /></el-icon>
                自动对话
              </el-button>
              <el-button size="small" type="info" @click="getNextSpeaker" :disabled="!isScriptReady || isTyping || isSending">
                <el-icon><ArrowRight /></el-icon>
                {{ isTyping ? '角色发言中...' : '调度下一个角色' }}
              </el-button>
              <el-button size="small" type="warning" @click="goToScript">
                <el-icon><Edit /></el-icon>
                重新创建剧本
              </el-button>
              <el-button size="small" type="danger" @click="endScript" :disabled="!isScriptReady">
                <el-icon><Close /></el-icon>
                结束当前剧本
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 自动对话设置对话框 -->
    <el-dialog v-model="autoDialogVisible" title="自动对话设置" width="400px">
      <el-form :model="autoForm" label-width="80px">
        <el-form-item label="对话轮数">
          <el-input-number v-model="autoForm.rounds" :min="1" :max="20" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="autoDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="startAutoConversation">开始</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, nextTick, inject } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import apiService from '../services/api.js'

export default {
  name: 'ChatInterface',
  setup() {
    const router = useRouter()
    const showLoading = inject('showLoading')
    const hideLoading = inject('hideLoading')

    const chatHistoryRef = ref()
    const isScriptReady = ref(false)
    const isSending = ref(false)
    const isTyping = ref(false)
    const typingSpeaker = ref('')
    const currentMessage = ref('')
    const currentRound = ref(1)
    const chatHistory = ref([])
    const characters = ref([])
    const nextSpeaker = ref('')
    const autoDialogVisible = ref(false)
    const shouldUserSpeak = ref(true) // 判断是否该用户发言
    const scriptEnded = ref(false) // 标记剧本是否已结束

    const autoForm = ref({
      rounds: 5
    })

    // 检查剧本状态
    const checkScriptStatus = async () => {
      try {
        const systemInfo = await apiService.getSystemInfo()
        if (systemInfo.success && systemInfo.initialized) {
          isScriptReady.value = true
          scriptEnded.value = false // 有剧本时，清除结束状态
          if (systemInfo.characters) {
            characters.value = systemInfo.characters
          }
        } else {
          // 如果后端没有初始化的剧本，但前端还没标记为结束，说明是初始状态
          if (!scriptEnded.value) {
            isScriptReady.value = false
            characters.value = []
          }
        }
      } catch (error) {
        console.error('检查剧本状态失败:', error)
        isScriptReady.value = false
      }
    }

    // 加载对话历史
    const loadHistory = async () => {
      try {
        const result = await apiService.getHistory()
        if (result.success) {
          chatHistory.value = result.history || []
          
          // 根据对话历史判断是否该用户发言
          if (chatHistory.value.length > 0) {
            const lastMessage = chatHistory.value[chatHistory.value.length - 1]
            // 如果最后一条消息不是用户发的，则轮到用户发言
            shouldUserSpeak.value = !isUserMessage(lastMessage)
          } else {
            shouldUserSpeak.value = true
          }
          
          await scrollToBottom()
        }
      } catch (error) {
        console.error('加载历史失败:', error)
        ElMessage.error('加载对话历史失败')
      }
    }

    // 滚动到底部
    const scrollToBottom = async () => {
      await nextTick()
      if (chatHistoryRef.value) {
        chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight
      }
    }

    // 判断是否为用户消息
    const isUserMessage = (message) => {
      return typeof message === 'string' && (message.startsWith('我：') || message.includes('我：'))
    }

    // 判断是否为系统消息
    const isSystemMessage = (message) => {
      return typeof message === 'string' && message.startsWith('系统：')
    }

    // 获取消息头像
    const getMessageAvatar = (message) => {
      return isUserMessage(message) ? '👤' : '🤖'
    }

    // 获取发言者名称
    const getSpeakerName = (message) => {
      if (typeof message === 'string') {
        const match = message.match(/^([^：]+)：/)
        return match ? match[1] : '未知'
      }
      return '未知'
    }

    // 获取消息文本内容
    const getMessageText = (message) => {
      if (typeof message === 'string') {
        const match = message.match(/^[^：]+：(.+)/)
        return match ? match[1] : message
      }
      return message
    }

    // 格式化时间
    const formatTime = (date) => {
      return date.toLocaleTimeString('zh-CN', { hour12: false })
    }

    // 发送消息
    const sendMessage = async () => {
      if (!currentMessage.value.trim() || !isScriptReady.value || isSending.value) {
        return
      }

      try {
        isSending.value = true
        shouldUserSpeak.value = false
        
        // 用户发言
        const userResult = await apiService.userSpeak(currentMessage.value, currentRound.value)
        if (userResult.success) {
          chatHistory.value.push(userResult.formatted_message)
          currentMessage.value = ''
          await scrollToBottom()

          // 短暂延迟后获取AI回应
          setTimeout(async () => {
            await getAIResponse()
          }, 500)
        }
      } catch (error) {
        ElMessage.error(error.message || '发送消息失败')
        console.error('发送消息失败:', error)
        shouldUserSpeak.value = true
      } finally {
        isSending.value = false
      }
    }

    // 获取AI回应(按照剧情调度下一个角色)
    const getAIResponse = async () => {
      try {
        isTyping.value = true
        shouldUserSpeak.value = false
        
        console.log('调用getAIResponse，当前轮次:', currentRound.value)
        
        // 获取下一个发言者
        const nextSpeakerResult = await apiService.getNextSpeaker(currentRound.value)
        console.log('下一个发言者结果:', nextSpeakerResult)
        
        if (nextSpeakerResult.success && nextSpeakerResult.speaker_type === 'ai' && nextSpeakerResult.next_speaker) {
          typingSpeaker.value = nextSpeakerResult.next_speaker
          nextSpeaker.value = nextSpeakerResult.next_speaker
          
          console.log('调度AI角色发言:', nextSpeakerResult.next_speaker)

          // AI发言
          const aiResult = await apiService.aiSpeak(
            nextSpeakerResult.next_speaker, 
            currentRound.value,
            `这是第${currentRound.value}轮对话，按照剧情发展，现在轮到${nextSpeakerResult.next_speaker}发言`
          )
          
          console.log('AI发言结果:', aiResult)
          
          if (aiResult.success) {
            chatHistory.value.push(aiResult.message)
            currentRound.value++
            shouldUserSpeak.value = true // AI发言后，轮到用户
            await scrollToBottom()
            console.log('AI发言成功，轮到用户发言')
          }
        } else if (nextSpeakerResult.success && nextSpeakerResult.speaker_type === 'user') {
          // 如果按照剧情下一个是用户，直接提示
          console.log('剧情调度结果：下一个是用户')
          shouldUserSpeak.value = true
        } else {
          console.log('无法确定下一个发言者，默认轮到用户')
          shouldUserSpeak.value = true
        }
      } catch (error) {
        ElMessage.error(error.message || '剧情调度失败')
        console.error('获取AI回应失败:', error)
        shouldUserSpeak.value = true // 出错时让用户继续
      } finally {
        isTyping.value = false
        typingSpeaker.value = ''
      }
    }

    // 跳过当前轮次(与用户发言完毕逻辑相同)
    const skipTurn = async () => {
      try {
        isSending.value = true
        shouldUserSpeak.value = false
        
        console.log('用户跳过发言，当前轮次:', currentRound.value)
        
        // 发送换行符给后端，相当于用户输入了\n
        const userResult = await apiService.userSpeak('\n', currentRound.value, 'speak')
        console.log('跳过发言结果:', userResult)
        
        if (userResult.success) {
          // 不在聊天框显示跳过消息，但调度逻辑和发言完毕一样
          
          // 短暂延迟后获取AI回应，与发言完毕逻辑一致
          setTimeout(async () => {
            await getAIResponse()
          }, 500)
        }
      } catch (error) {
        ElMessage.error(error.message || '调度失败')
        console.error('跳过发言失败:', error)
        shouldUserSpeak.value = true
      } finally {
        isSending.value = false
      }
    }

    // 获取下一个发言者(与跳过逻辑相同)
    const getNextSpeaker = async () => {
      await skipTurn()
    }

    // 清空对话
    const clearChat = async () => {
      try {
        await ElMessageBox.confirm(
          '确定要清空所有对话记录吗？（不会结束剧本，角色设定仍然保留）', 
          '清空对话历史', 
          {
            type: 'warning',
            confirmButtonText: '确定清空',
            cancelButtonText: '取消'
          }
        )
        
        await apiService.clearHistory()
        chatHistory.value = []
        currentRound.value = 1
        nextSpeaker.value = ''
        shouldUserSpeak.value = true
        currentMessage.value = ''
        ElMessage.success('对话历史已清空，剧本设定保持不变')
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('清空失败')
        }
      }
    }

    // 自动对话
    const autoConversation = () => {
      autoDialogVisible.value = true
    }

    const startAutoConversation = async () => {
      try {
        autoDialogVisible.value = false
        showLoading(`开始${autoForm.value.rounds}轮自动对话...`)
        
        const result = await apiService.startConversation(autoForm.value.rounds)
        if (result.success) {
          ElMessage.success('自动对话已启动')
          // 定期刷新历史记录
          const refreshInterval = setInterval(async () => {
            await loadHistory()
          }, 2000)
          
          // 10秒后停止刷新
          setTimeout(() => {
            clearInterval(refreshInterval)
            hideLoading()
          }, 10000)
        }
      } catch (error) {
        ElMessage.error(error.message || '启动自动对话失败')
        hideLoading()
      }
    }

    // 开始对话
    const startChat = () => {
      shouldUserSpeak.value = true
      ElMessage.info('请输入您的第一句台词开始对话')
    }

    // 跳转到剧本创建
    const goToScript = () => {
      scriptEnded.value = false // 重置剧本结束状态
      router.push('/script')
    }

    // 结束当前剧本
    const endScript = async () => {
      try {
        await ElMessageBox.confirm(
          '确定要结束当前剧本吗？结束后将清空所有对话记录和角色设定，需要重新创建剧本才能继续。', 
          '结束剧本确认', 
          {
            type: 'warning',
            confirmButtonText: '确定结束',
            cancelButtonText: '取消',
            dangerouslyUseHTMLString: false
          }
        )
        
        showLoading('正在结束剧本...')
        
        // 清空后端历史记录
        await apiService.clearHistory()
        
        // 重置所有前端状态
        resetAllStates()
        
        ElMessage.success('剧本已结束，您可以创建新的剧本开始全新的故事')
        
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('结束剧本失败')
          console.error('结束剧本失败:', error)
        }
      } finally {
        hideLoading()
      }
    }

    // 重置所有状态
    const resetAllStates = () => {
      // 重置对话相关状态
      chatHistory.value = []
      currentRound.value = 1
      nextSpeaker.value = ''
      shouldUserSpeak.value = true
      currentMessage.value = ''
      
      // 重置UI状态
      isTyping.value = false
      isSending.value = false
      typingSpeaker.value = ''
      
              // 重置剧本状态
        isScriptReady.value = false
        characters.value = []
        scriptEnded.value = true
        
        // 触发连接状态检查，确保状态同步
        if (checkConnection) {
          checkConnection()
        }
        
        console.log('所有状态已重置，剧本已完全结束')
    }

    onMounted(async () => {
      await checkScriptStatus()
      await loadHistory()
      
      // 如果有剧本但没有对话历史，则提示开始对话
      if (isScriptReady.value && chatHistory.value.length === 0) {
        shouldUserSpeak.value = true
      }
    })

    return {
      chatHistoryRef,
      isScriptReady,
      isSending,
      isTyping,
      typingSpeaker,
      currentMessage,
      currentRound,
      chatHistory,
      characters,
      nextSpeaker,
      shouldUserSpeak,
      scriptEnded,
      autoDialogVisible,
      autoForm,
      loadHistory,
      isUserMessage,
      isSystemMessage,
      getMessageAvatar,
      getSpeakerName,
      getMessageText,
      formatTime,
      sendMessage,
      skipTurn,
      getNextSpeaker,
      clearChat,
      autoConversation,
      startAutoConversation,
      startChat,
      goToScript,
      endScript
    }
  }
}
</script>

<style scoped>
.chat-interface {
  max-width: 1400px;
  margin: 0 auto;
}

.chat-card {
  height: calc(100vh - 140px);
}

.chat-card :deep(.el-card__body) {
  height: calc(100vh - 140px - 60px); /* 减去header高度 */
  padding: 0;
}

.chat-container {
  position: relative; /* 为绝对定位的子元素提供定位上下文 */
  height: 100%; /* 填满卡片body的全部高度 */
  box-sizing: border-box;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  font-weight: bold;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.chat-history {
  position: absolute;
  top: 16px;
  left: 16px;
  right: 16px;
  height: calc(70% - 24px); /* 70%减去上下边距 */
  overflow-y: auto;
  padding: 16px;
  background: #fafbfc;
  border-radius: 8px;
}

.messages-container {
  min-height: 100%;
  padding-bottom: 20px;
}

.empty-chat {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 300px;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  animation: messageSlideIn 0.3s ease-out;
}

.user-message {
  flex-direction: row-reverse;
}

.user-message .message-content {
  background: #409EFF;
  color: white;
  border-radius: 18px 4px 18px 18px;
}

.ai-message .message-content {
  background: #f0f2f5;
  color: #303133;
  border-radius: 4px 18px 18px 18px;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  position: relative;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  font-size: 12px;
  opacity: 0.8;
}

.speaker-name {
  font-weight: bold;
}

.message-text {
  line-height: 1.5;
}

.typing-indicator {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  animation: fadeIn 0.5s ease-in-out;
}

.typing-content {
  background: #f0f2f5;
  padding: 12px 16px;
  border-radius: 4px 18px 18px 18px;
  font-style: italic;
  color: #909399;
}

.typing-dots span {
  animation: typingDots 1.4s infinite;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

.message-input {
  position: absolute;
  bottom: 16px;
  left: 16px;
  right: 16px;
  height: calc(30% - 24px); /* 30%减去上下边距 */
  border-top: 2px solid #e4e7ed;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
  box-sizing: border-box;
}

.input-wrapper {
  margin-bottom: 12px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.input-tips {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #909399;
}

.round-info {
  font-weight: bold;
  color: #409EFF;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.info-panel {
  height: calc(100vh - 140px);
  overflow-y: auto;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}

.character-section,
.stats-section,
.actions-section {
  margin-bottom: 24px;
}

.character-section h4,
.stats-section h4,
.actions-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 14px;
  font-weight: bold;
}

.characters-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.character-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.character-item.active-speaker {
  background: #f0f9ff;
  border: 1px solid #409EFF;
}

.character-avatar {
  font-size: 20px;
}

.character-name {
  font-weight: bold;
  font-size: 14px;
}

.character-type {
  font-size: 12px;
  color: #909399;
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.no-characters {
  text-align: center;
  padding: 20px;
}

/* 动画效果 */
@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes typingDots {
  0%, 20% {
    opacity: 0;
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}

/* 状态提示样式 */
.status-tip {
  text-align: center;
  margin: 16px 0;
  padding: 8px 16px;
  font-size: 12px;
  color: #909399;
  background: rgba(144, 147, 153, 0.1);
  border-radius: 16px;
  display: inline-block;
  width: auto;
  margin-left: 50%;
  transform: translateX(-50%);
  border: 1px solid rgba(144, 147, 153, 0.2);
  animation: fadeInSlide 0.3s ease-out;
}

.status-tip.next-action {
  background: rgba(64, 158, 255, 0.1);
  color: #409EFF;
  border-color: rgba(64, 158, 255, 0.3);
  font-weight: 500;
}

.status-tip.warning {
  background: rgba(245, 108, 108, 0.1);
  color: #F56C6C;
  border-color: rgba(245, 108, 108, 0.3);
}

.status-tip.system-message {
  background: rgba(103, 194, 58, 0.1);
  color: #67C23A;
  border-color: rgba(103, 194, 58, 0.3);
  font-weight: 500;
  margin: 8px 0;
}

.status-tip span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* 状态提示动画 */
@keyframes fadeInSlide {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .chat-interface {
    padding: 0 10px;
  }
}

@media (max-width: 768px) {
  .message-content {
    max-width: 85%;
  }
  
  .input-actions {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .action-buttons {
    justify-content: center;
  }
  
  .status-tip {
    font-size: 11px;
    padding: 6px 12px;
    margin: 12px 0;
    max-width: 90%;
  }
  
  .status-tip span {
    gap: 2px;
  }
}

/* 剧本结束状态样式 */
.script-ended-notice {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 400px;
  padding: 40px 20px;
}

.script-ended-notice .el-result {
  padding: 20px;
}
</style> 