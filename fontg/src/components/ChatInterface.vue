<template>
  <div class="chat-interface">
    <el-row :gutter="20">
      <!-- 场景图片对话区域 -->
      <el-col :span="18">
        <el-card class="scene-card" shadow="hover">
          <template #header>
            <div class="chat-header">
              <div class="header-info">
                <el-icon><ChatDotRound /></el-icon>
                <span>剧本对话</span>
                <el-tag v-if="isScriptReady" type="success" size="small">剧本已就绪</el-tag>
                <el-tag v-else type="warning" size="small">请先创建剧本</el-tag>
              </div>
              <div class="header-actions">
                <el-button size="small" @click="generateSceneImage" :loading="generatingImage">
                  <el-icon><Picture /></el-icon>
                  生成场景图片
                </el-button>
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

          <!-- 场景图片容器 -->
          <div class="scene-container">
            <!-- 背景图片 -->
            <div 
              v-if="sceneImageUrl" 
              class="scene-background"
              :style="{ backgroundImage: `url(${sceneImageUrl})` }"
            >
              <!-- 透明对话显示容器 -->
              <div 
                v-show="showDialogueOverlay && currentDialogue"
                class="dialogue-overlay"
                :class="{ 'fade-in': showDialogueOverlay }"
              >
                <div class="dialogue-content">
                  <div class="speaker-info">
                    <el-avatar :size="40">{{ currentSpeakerAvatar }}</el-avatar>
                    <span class="speaker-name">{{ currentSpeakerName }}</span>
                  </div>
                  <div class="dialogue-text">{{ currentDialogue }}</div>
                </div>
              </div>

              <!-- 空状态显示 -->
              <div v-if="!isScriptReady" class="scene-empty-state">
                <el-empty description="请先创建剧本开始对话">
                  <el-button type="primary" @click="goToScript">
                    <el-icon><Edit /></el-icon>
                    创建剧本
                  </el-button>
                </el-empty>
              </div>

              <!-- 剧本结束状态 -->
              <div v-else-if="scriptEnded" class="scene-empty-state">
                <el-empty description="剧本已结束">
                  <el-button type="primary" @click="goToScript">
                    <el-icon><Edit /></el-icon>
                    创建新剧本
                  </el-button>
                </el-empty>
              </div>
            </div>

            <!-- 无图片时的占位 -->
            <div v-else class="scene-placeholder">
              <el-empty description="暂无场景图片" :image-size="200">
                <el-button 
                  v-if="isScriptReady" 
                  type="primary" 
                  @click="generateSceneImage"
                  :loading="generatingImage"
                >
                  <el-icon><Picture /></el-icon>
                  生成场景图片
                </el-button>
                <el-button v-else type="primary" @click="goToScript">
                  <el-icon><Edit /></el-icon>
                  创建剧本
                </el-button>
              </el-empty>
                        </div>

            <!-- 消息输入区域 -->
            <div class="message-input-container">
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
                    <span class="tip-text">Ctrl + Enter 快速发送 | 🎤 语音录音 | 📋 智能推荐台词</span>
                    <span class="round-info">第 {{ currentRound }} 轮对话</span>
                  </div>
                  <div class="action-buttons">
                    <el-button 
                      type="info" 
                      @click="showDialogueOptions"
                      :disabled="!isScriptReady || isSending"
                    >
                      <el-icon><List /></el-icon>
                      选择台词
                    </el-button>
                    <el-button 
                      type="default" 
                      @click="skipTurn"
                      :disabled="!isScriptReady || isSending"
                    >
                      {{ isSending ? '调度中...' : '跳过发言' }}
                    </el-button>
                    <el-button 
                      :type="isRecording ? 'danger' : 'warning'"
                      @click="toggleVoiceRecording"
                      :disabled="!isScriptReady || isSending"
                    >
                      <el-icon><Microphone /></el-icon>
                      {{ isRecording ? '停止录音' : '开始录音' }}
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
                  <div class="character-name">
                    <span v-if="character.type === 'user'">
                      {{ hasUserCharacter ? `我（${userCharacter}）` : '我' }}
                    </span>
                    <span v-else>{{ character.name }}</span>
                  </div>
                  <div class="character-type">{{ character.type === 'user' ? '用户主角' : 'AI角色' }}</div>
                  <!-- 显示重置角色按钮 -->
                  <div v-if="character.type === 'user' && hasUserCharacter" class="character-actions">
                    <el-button 
                      size="small" 
                      type="text" 
                      @click="resetUserCharacter"
                      title="重置角色，重新选择"
                    >
                      🔄 重置
                    </el-button>
                  </div>
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

    <!-- 台词选择对话框 -->
    <el-dialog v-model="dialogueOptionsVisible" title="选择台词" width="500px" center>
      <div v-if="loadingOptions" class="loading-options">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <p>正在生成台词选项...</p>
      </div>
      <div v-else-if="dialogueOptions.length > 0" class="dialogue-options">
        <p class="options-tip">💡 根据当前剧情为您推荐以下台词：</p>
        <div 
          v-for="(option, index) in dialogueOptions" 
          :key="index"
          class="option-item"
          @click="selectOption(option)"
        >
          <div class="option-content">
            <div class="option-icon">{{ getOptionIcon(option, index) }}</div>
            <div class="option-text">{{ getOptionText(option) }}</div>
            <div class="option-type">{{ getOptionType(option, index) }}</div>
          </div>
        </div>
      </div>
      <div v-else class="no-options">
        <el-empty description="暂无推荐台词" :image-size="60">
          <el-button type="primary" @click="dialogueOptionsVisible = false">关闭</el-button>
        </el-empty>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogueOptionsVisible = false">取消</el-button>
          <el-button type="info" @click="refreshOptions" :loading="loadingOptions">
            <el-icon><Refresh /></el-icon>
            重新生成
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, nextTick, inject } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import apiService from '../services/api.js'

export default {
  name: 'ChatInterface',
  setup() {
    const router = useRouter()
    const checkConnection = inject('checkConnection')
    const showLoading = inject('showLoading')
    const hideLoading = inject('hideLoading')

    const chatHistoryRef = ref()
    const isScriptReady = ref(false)
    const isSending = ref(false)
    const isTyping = ref(false)
    const isRecording = ref(false)
    const typingSpeaker = ref('')
    const currentMessage = ref('')
    const currentRound = ref(1)
    const chatHistory = ref([])
    const characters = ref([])
    const nextSpeaker = ref('')
    const autoDialogVisible = ref(false)
    const shouldUserSpeak = ref(true) // 判断是否该用户发言
    const scriptEnded = ref(false) // 标记剧本是否已结束
    const speakerDisplayTimer = ref(null) // 发言人提示显示计时器
    const dialogueOptionsVisible = ref(false) // 台词选择对话框显示状态
    const dialogueOptions = ref([]) // 台词选项列表
    const loadingOptions = ref(false) // 加载台词选项状态
    
    // 用户角色相关
    const userCharacter = ref(null) // 用户当前扮演的角色
    const userCharacterInfo = ref(null) // 用户角色的详细信息
    const hasUserCharacter = ref(false) // 是否已选择角色

    // 场景图片和对话显示相关
    const sceneImageUrl = ref(null) // 场景图片URL
    const generatingImage = ref(false) // 是否正在生成图片
    const showDialogueOverlay = ref(false) // 是否显示对话overlay
    const currentDialogue = ref('') // 当前显示的对话内容
    const currentSpeakerName = ref('') // 当前说话人名字
    const currentSpeakerAvatar = ref('') // 当前说话人头像
    const dialogueTimer = ref(null) // 对话显示计时器

    const autoForm = ref({
      rounds: 5
    })

    // 检查剧本状态
    const checkScriptStatus = async () => {
      try {
        const systemInfo = await apiService.getSystemInfo()
        if (systemInfo.success && systemInfo.initialized) {
          const wasReady = isScriptReady.value
          isScriptReady.value = true
          scriptEnded.value = false // 有剧本时，清除结束状态
          if (systemInfo.characters) {
            characters.value = systemInfo.characters
          }
          
          // 如果剧本状态从未就绪变为就绪，重新加载用户角色信息
          if (!wasReady) {
            await loadUserCharacter()
          }
        } else {
          // 如果后端没有初始化的剧本，但前端还没标记为结束，说明是初始状态
          if (!scriptEnded.value) {
            isScriptReady.value = false
            characters.value = []
            // 清除用户角色信息
            userCharacter.value = null
            userCharacterInfo.value = null
            hasUserCharacter.value = false
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

    // 获取用户角色信息
    const loadUserCharacter = async () => {
      try {
        const result = await apiService.getUserCharacter()
        if (result.success) {
          userCharacter.value = result.user_character
          userCharacterInfo.value = result.character_info
          hasUserCharacter.value = result.has_character
          console.log('用户角色信息:', {
            character: userCharacter.value,
            hasCharacter: hasUserCharacter.value
          })
        }
      } catch (error) {
        console.error('获取用户角色失败:', error)
        // 不显示错误消息，因为用户可能还没选择角色
      }
    }

    // 重置用户角色
    const resetUserCharacter = async () => {
      try {
        const result = await apiService.resetUserCharacter()
        if (result.success) {
          userCharacter.value = null
          userCharacterInfo.value = null
          hasUserCharacter.value = false
          ElMessage.success('角色已重置，可以重新选择')
        }
      } catch (error) {
        console.error('重置用户角色失败:', error)
        ElMessage.error('重置角色失败')
      }
    }

    // 刷新全部状态（用于页面激活或路由变化时）
    const refreshAllStatus = async () => {
      try {
        await checkScriptStatus()
        await loadHistory()
        await loadUserCharacter()
        console.log('✅ 全部状态已刷新')
      } catch (error) {
        console.error('刷新状态失败:', error)
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
          
          // 显示用户对话内容
          const userDisplayName = hasUserCharacter.value ? userCharacter.value : '我'
          showDialogue(currentMessage.value, userDisplayName, '👤')
          
          currentMessage.value = ''
          await scrollToBottom()

          // 清除之前的定时器
          if (speakerDisplayTimer.value) {
            clearTimeout(speakerDisplayTimer.value)
            speakerDisplayTimer.value = null
          }
          
          // 立即查询下一个发言人并显示提示
          try {
            const nextSpeakerResult = await apiService.getNextSpeaker(currentRound.value)
            if (nextSpeakerResult.success && nextSpeakerResult.next_speaker) {
              nextSpeaker.value = nextSpeakerResult.next_speaker
              console.log('预显示下一个发言人:', nextSpeakerResult.next_speaker)
            }
          } catch (error) {
            console.error('查询下一个发言人失败:', error)
          }

          // 短暂延迟后获取AI回应
          setTimeout(async () => {
            await getAIResponse()
          }, 1000) // 增加延迟时间让用户看到提示
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
        console.log('当前nextSpeaker:', nextSpeaker.value)
        
        // 如果已经有nextSpeaker且是AI角色，直接使用
        if (nextSpeaker.value && nextSpeaker.value !== '我') {
          const aiSpeaker = nextSpeaker.value
          typingSpeaker.value = aiSpeaker
          
          console.log('使用预设的AI角色发言:', aiSpeaker)

          // AI发言
          const aiResult = await apiService.aiSpeak(
            aiSpeaker, 
            currentRound.value,
            `这是第${currentRound.value}轮对话，按照剧情发展，现在轮到${aiSpeaker}发言`
          )
          
          console.log('AI发言结果:', aiResult)
          
          if (aiResult.success) {
            chatHistory.value.push(aiResult.message)
            
            // 显示AI对话内容
            const aiMessage = getMessageText(aiResult.message)
            showDialogue(aiMessage, aiSpeaker, '🤖')
            
            currentRound.value++
            shouldUserSpeak.value = true // AI发言后，轮到用户
            await scrollToBottom()
            console.log('AI发言成功，轮到用户发言')
            
            // 设置10秒延迟后再显示"下一个发言人：我"
            if (speakerDisplayTimer.value) {
              clearTimeout(speakerDisplayTimer.value)
            }
            speakerDisplayTimer.value = setTimeout(() => {
              nextSpeaker.value = '我' // 10秒后设置下一个发言人为用户
              console.log('10秒后显示：下一个发言人是我')
            }, 10000)
          }
        } else {
          // 如果没有预设，重新获取下一个发言者
          const nextSpeakerResult = await apiService.getNextSpeaker(currentRound.value)
          console.log('重新获取下一个发言者结果:', nextSpeakerResult)
          
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
              
              // 显示AI对话内容
              const aiMessage = getMessageText(aiResult.message)
              showDialogue(aiMessage, nextSpeakerResult.next_speaker, '🤖')
              
              currentRound.value++
              shouldUserSpeak.value = true // AI发言后，轮到用户
              await scrollToBottom()
              console.log('AI发言成功，轮到用户发言')
              
              // 设置10秒延迟后再显示"下一个发言人：我"
              if (speakerDisplayTimer.value) {
                clearTimeout(speakerDisplayTimer.value)
              }
              speakerDisplayTimer.value = setTimeout(() => {
                nextSpeaker.value = '我' // 10秒后设置下一个发言人为用户
                console.log('10秒后显示：下一个发言人是我')
              }, 10000)
            }
          } else if (nextSpeakerResult.success && nextSpeakerResult.speaker_type === 'user') {
            // 如果按照剧情下一个是用户，直接提示
            console.log('剧情调度结果：下一个是用户')
            shouldUserSpeak.value = true
            // 设置10秒延迟后再显示"下一个发言人：我"
            if (speakerDisplayTimer.value) {
              clearTimeout(speakerDisplayTimer.value)
            }
            speakerDisplayTimer.value = setTimeout(() => {
              nextSpeaker.value = '我' // 10秒后设置下一个发言人为用户
              console.log('10秒后显示：下一个发言人是我')
            }, 10000)
          } else {
            console.log('无法确定下一个发言者，默认轮到用户')
            shouldUserSpeak.value = true
            // 设置10秒延迟后再显示"下一个发言人：我"
            if (speakerDisplayTimer.value) {
              clearTimeout(speakerDisplayTimer.value)
            }
            speakerDisplayTimer.value = setTimeout(() => {
              nextSpeaker.value = '我' // 10秒后设置下一个发言人为用户
              console.log('10秒后显示：下一个发言人是我')
            }, 10000)
          }
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
          
          // 清除之前的定时器
          if (speakerDisplayTimer.value) {
            clearTimeout(speakerDisplayTimer.value)
            speakerDisplayTimer.value = null
          }
          
          // 立即查询下一个发言人并显示提示
          try {
            const nextSpeakerResult = await apiService.getNextSpeaker(currentRound.value)
            if (nextSpeakerResult.success && nextSpeakerResult.next_speaker) {
              nextSpeaker.value = nextSpeakerResult.next_speaker
              console.log('跳过后预显示下一个发言人:', nextSpeakerResult.next_speaker)
            }
          } catch (error) {
            console.error('查询下一个发言人失败:', error)
          }
          
          // 短暂延迟后获取AI回应，与发言完毕逻辑一致
          setTimeout(async () => {
            await getAIResponse()
          }, 1000) // 增加延迟时间让用户看到提示
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

    // 切换语音录音状态
    const toggleVoiceRecording = async () => {
      if (!isScriptReady.value || isSending.value) {
        return
      }

      try {
        if (!isRecording.value) {
          // 开始录音
          const startResult = await apiService.startVoiceRecording()
          if (startResult.success) {
            isRecording.value = true
            ElMessage.info('录音已开始，请说话...')
            console.log('开始录音成功')
          } else {
            ElMessage.error(startResult.error || '开始录音失败')
          }
        } else {
          // 停止录音并识别
          const stopResult = await apiService.stopVoiceRecording(currentRound.value)
          if (stopResult.success) {
            ElMessage.success(`语音识别成功：${stopResult.recognized_text}`)
            
            // 将识别结果添加到聊天历史
            chatHistory.value.push(stopResult.formatted_message)
            await scrollToBottom()

            // 清除之前的定时器
            if (speakerDisplayTimer.value) {
              clearTimeout(speakerDisplayTimer.value)
              speakerDisplayTimer.value = null
            }
            
            // 立即查询下一个发言人并显示提示
            try {
              const nextSpeakerResult = await apiService.getNextSpeaker(currentRound.value)
              if (nextSpeakerResult.success && nextSpeakerResult.next_speaker) {
                nextSpeaker.value = nextSpeakerResult.next_speaker
                console.log('语音输入后预显示下一个发言人:', nextSpeakerResult.next_speaker)
              }
            } catch (error) {
              console.error('查询下一个发言人失败:', error)
            }

            // 短暂延迟后获取AI回应
            setTimeout(async () => {
              await getAIResponse()
            }, 1000)
          } else {
            ElMessage.error(stopResult.error || '语音识别失败')
          }
          isRecording.value = false
        }
      } catch (error) {
        ElMessage.error(error.message || '语音操作失败')
        console.error('语音操作失败:', error)
        isRecording.value = false
      }
    }

    // 显示台词选择对话框
    const showDialogueOptions = async () => {
      if (!isScriptReady.value || isSending.value) {
        return
      }

      try {
        dialogueOptionsVisible.value = true
        loadingOptions.value = true
        dialogueOptions.value = []

        // 获取台词选项
        const result = await apiService.getDialogueOptions(currentRound.value)
        
        if (result.success && result.options && result.options.length > 0) {
          dialogueOptions.value = result.options
          console.log('获取台词选项成功:', result.options)
        } else {
          ElMessage.warning('未能获取到台词推荐，请重试')
          dialogueOptionsVisible.value = false
        }
      } catch (error) {
        ElMessage.error(error.message || '获取台词选项失败')
        console.error('获取台词选项失败:', error)
        dialogueOptionsVisible.value = false
      } finally {
        loadingOptions.value = false
      }
    }

    // 选择台词选项
    const selectOption = async (selectedText) => {
      if (!selectedText || isSending.value) {
        return
      }

      try {
        dialogueOptionsVisible.value = false
        isSending.value = true

        // 发送选择的台词
        const result = await apiService.selectDialogue(selectedText, currentRound.value)
        
        if (result.success) {
          // 显示更详细的选择信息
          if (result.character_name && result.character_name !== "我" && result.character_name !== "用户") {
            ElMessage.success(`🎭 已扮演 ${result.character_name}：${result.dialogue_content}`)
          } else {
            ElMessage.success(`已选择：${result.dialogue_content}`)
          }
          
          // 将选择的台词添加到聊天历史
          chatHistory.value.push(result.formatted_message)
          await scrollToBottom()

          // 更新用户角色信息（如果选择了角色）
          if (result.character_name && result.character_name !== "我" && result.character_name !== "用户") {
            await loadUserCharacter()
          }

          // 清除之前的定时器
          if (speakerDisplayTimer.value) {
            clearTimeout(speakerDisplayTimer.value)
            speakerDisplayTimer.value = null
          }
          
          // 立即查询下一个发言人并显示提示
          try {
            const nextSpeakerResult = await apiService.getNextSpeaker(currentRound.value)
            if (nextSpeakerResult.success && nextSpeakerResult.next_speaker) {
              nextSpeaker.value = nextSpeakerResult.next_speaker
              console.log('选择台词后预显示下一个发言人:', nextSpeakerResult.next_speaker)
            }
          } catch (error) {
            console.error('查询下一个发言人失败:', error)
          }

          // 短暂延迟后获取AI回应
          setTimeout(async () => {
            await getAIResponse()
          }, 1000)
        } else {
          ElMessage.error(result.error || '选择台词失败')
        }
      } catch (error) {
        ElMessage.error(error.message || '选择台词失败')
        console.error('选择台词失败:', error)
      } finally {
        isSending.value = false
      }
    }

    // 重新生成台词选项
    const refreshOptions = async () => {
      if (loadingOptions.value) {
        return
      }

      try {
        loadingOptions.value = true
        dialogueOptions.value = []

        // 重新获取台词选项
        const result = await apiService.getDialogueOptions(currentRound.value)
        
        if (result.success && result.options && result.options.length > 0) {
          dialogueOptions.value = result.options
          ElMessage.success('台词选项已更新')
          console.log('重新生成台词选项成功:', result.options)
        } else {
          ElMessage.warning('未能生成新的台词推荐')
        }
      } catch (error) {
        ElMessage.error(error.message || '重新生成台词选项失败')
        console.error('重新生成台词选项失败:', error)
      } finally {
        loadingOptions.value = false
      }
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

    // 页面可见性变化处理函数
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        console.log('页面变为可见，刷新状态...')
        refreshAllStatus()
      }
    }

    onMounted(async () => {
      // 使用统一的状态刷新方法
      await refreshAllStatus()
      
      // 如果有剧本但没有对话历史，则提示开始对话
      if (isScriptReady.value && chatHistory.value.length === 0) {
        shouldUserSpeak.value = true
      }
      
      // 添加页面可见性变化监听器
      document.addEventListener('visibilitychange', handleVisibilityChange)
    })

    onUnmounted(async () => {
      // 移除页面可见性监听器
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      
      // 清理定时器
      if (speakerDisplayTimer.value) {
        clearTimeout(speakerDisplayTimer.value)
        speakerDisplayTimer.value = null
      }
      
      // 如果正在录音，停止录音
      if (isRecording.value) {
        try {
          await apiService.stopVoiceRecording(currentRound.value)
          isRecording.value = false
          console.log('组件卸载时停止录音')
        } catch (error) {
          console.error('组件卸载时停止录音失败:', error)
        }
      }
    })

    // 获取台词选项的图标
    const getOptionIcon = (option, index) => {
      const match = option.match(/^\[([^\]]+)\]/)
      if (match) {
        const character = match[1]
        // 根据角色名返回对应图标
        const iconMap = {
          '黄盖': '🔥',
          '周瑜': '🎯', 
          '孙权': '👑',
          '诸葛亮': '🎭',
          '刘备': '⚔️',
          '关羽': '🗡️',
          '张飞': '💪',
          '曹操': '🏴',
          '用户': '👤'
        }
        return iconMap[character] || '🎲'
      }
      return index === 0 ? '💪' : '🤔' // 兼容旧格式
    }

    // 获取台词选项的文本内容
    const getOptionText = (option) => {
      const match = option.match(/^\[([^\]]+)\]\s*(.+)/)
      if (match) {
        return match[2] // 返回台词内容
      }
      return option // 兼容旧格式
    }

    // 获取台词选项的类型标签
    const getOptionType = (option, index) => {
      const match = option.match(/^\[([^\]]+)\]/)
      if (match) {
        return match[1] // 返回角色名
      }
      return index === 0 ? '积极进取' : '谨慎思考' // 兼容旧格式
    }

    // 生成场景图片
    const generateSceneImage = async () => {
      if (!isScriptReady.value || generatingImage.value) {
        return
      }

      try {
        generatingImage.value = true
        showLoading('正在生成场景图片，请稍候...')
        
        const result = await apiService.generateSceneImage()
        
        if (result.success) {
          // 更新场景图片URL
          sceneImageUrl.value = apiService.getSceneImageUrl()
          ElMessage.success('场景图片生成成功！')
        } else {
          ElMessage.error(result.error || '场景图片生成失败')
        }
      } catch (error) {
        ElMessage.error(error.message || '场景图片生成失败')
        console.error('生成场景图片失败:', error)
      } finally {
        generatingImage.value = false
        hideLoading()
      }
    }

    // 显示对话内容
    const showDialogue = (message, speakerName, speakerAvatar) => {
      // 清除之前的计时器
      if (dialogueTimer.value) {
        clearTimeout(dialogueTimer.value)
        dialogueTimer.value = null
      }

      // 设置对话内容
      currentDialogue.value = message
      currentSpeakerName.value = speakerName
      currentSpeakerAvatar.value = speakerAvatar
      
      // 显示对话overlay
      showDialogueOverlay.value = true

      // 10秒后隐藏
      dialogueTimer.value = setTimeout(() => {
        showDialogueOverlay.value = false
        currentDialogue.value = ''
        currentSpeakerName.value = ''
        currentSpeakerAvatar.value = ''
        dialogueTimer.value = null
      }, 10000)
    }

    // 隐藏对话overlay
    const hideDialogue = () => {
      if (dialogueTimer.value) {
        clearTimeout(dialogueTimer.value)
        dialogueTimer.value = null
      }
      showDialogueOverlay.value = false
      currentDialogue.value = ''
      currentSpeakerName.value = ''
      currentSpeakerAvatar.value = ''
    }

    return {
      chatHistoryRef,
      isScriptReady,
      isSending,
      isTyping,
      isRecording,
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
      dialogueOptionsVisible,
      dialogueOptions,
      loadingOptions,
      userCharacter,
      userCharacterInfo,
      hasUserCharacter,
      loadHistory,
      loadUserCharacter,
      resetUserCharacter,
      refreshAllStatus,
      isUserMessage,
      isSystemMessage,
      getMessageAvatar,
      getSpeakerName,
      getMessageText,
      formatTime,
      sendMessage,
      skipTurn,
      toggleVoiceRecording,
      showDialogueOptions,
      selectOption,
      refreshOptions,
      getNextSpeaker,
      clearChat,
      autoConversation,
      startAutoConversation,
      startChat,
      goToScript,
      endScript,
      getOptionIcon,
      getOptionText,
      getOptionType,
      generateSceneImage,
      showDialogue,
      hideDialogue
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

.action-buttons .el-button--warning {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  border-color: #f59e0b;
  color: white;
  transition: all 0.3s ease;
}

.action-buttons .el-button--warning:hover {
  background: linear-gradient(135deg, #d97706, #b45309);
  border-color: #d97706;
  transform: translateY(-1px);
}

.action-buttons .el-button--warning.is-loading {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  border-color: #ef4444;
}

.action-buttons .el-button--danger {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  border-color: #ef4444;
  color: white;
  transition: all 0.3s ease;
  animation: recording-pulse 1.5s infinite;
}

.action-buttons .el-button--danger:hover {
  background: linear-gradient(135deg, #dc2626, #b91c1c);
  border-color: #dc2626;
  transform: translateY(-1px);
}

.action-buttons .el-button--info {
  background: linear-gradient(135deg, #909399, #73767a);
  border-color: #909399;
  color: white;
  transition: all 0.3s ease;
}

.action-buttons .el-button--info:hover {
  background: linear-gradient(135deg, #73767a, #606266);
  border-color: #73767a;
  transform: translateY(-1px);
}

@keyframes recording-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(239, 68, 68, 0);
  }
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

.character-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.character-name {
  font-weight: bold;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.character-type {
  font-size: 12px;
  color: #909399;
}

.character-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
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

.status-tip.next-speaker {
  background: rgba(230, 162, 60, 0.1);
  color: #E6A23C;
  border-color: rgba(230, 162, 60, 0.3);
  font-weight: 600;
  font-size: 13px;
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

/* 台词选择对话框样式 */
.loading-options {
  text-align: center;
  padding: 40px 20px;
}

.loading-options .loading-icon {
  font-size: 24px;
  color: #409EFF;
  margin-bottom: 10px;
  animation: rotate 2s linear infinite;
}

.dialogue-options {
  padding: 20px 0;
}

.options-tip {
  text-align: center;
  margin-bottom: 20px;
  color: #606266;
  font-size: 14px;
}

.option-item {
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.option-item:hover {
  transform: translateY(-2px);
}

.option-content {
  display: flex;
  align-items: center;
  padding: 16px;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  background: linear-gradient(135deg, #f8f9fa, #ffffff);
  transition: all 0.3s ease;
}

.option-item:hover .option-content {
  border-color: #409EFF;
  background: linear-gradient(135deg, #ecf5ff, #ffffff);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.1);
}

.option-icon {
  font-size: 24px;
  margin-right: 12px;
  min-width: 32px;
}

.option-text {
  flex: 1;
  font-size: 15px;
  color: #303133;
  line-height: 1.4;
  font-weight: 500;
}

.option-type {
  font-size: 12px;
  color: #909399;
  background: rgba(144, 147, 153, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
  white-space: nowrap;
}

.option-item:nth-child(2) .option-content {
  background: linear-gradient(135deg, #fff7e6, #ffffff);
}

.option-item:nth-child(2):hover .option-content {
  border-color: #E6A23C;
  background: linear-gradient(135deg, #fdf6ec, #ffffff);
  box-shadow: 0 4px 12px rgba(230, 162, 60, 0.1);
}

.option-item:nth-child(2) .option-type {
  background: rgba(230, 162, 60, 0.1);
  color: #E6A23C;
}

.no-options {
  padding: 20px;
}

.script-ended-notice .el-result {
  padding: 20px;
}
</style> 