import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 600000, // 10分钟超时，与Vite代理保持一致
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    console.log('API请求:', config.method?.toUpperCase(), config.url, config.data)
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    console.log('API响应:', response.config.url, response.data)
    return response
  },
  error => {
    console.error('响应错误:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// API服务类
class ApiService {
  // 获取系统状态
  async getStatus() {
    try {
      const response = await api.get('/status')
      return response.data
    } catch (error) {
      throw new Error(`获取系统状态失败: ${error.response?.data?.error || error.message}`)
    }
  }

  // 获取系统详细信息
  async getSystemInfo() {
    try {
      const response = await api.get('/system-info')
      return response.data
    } catch (error) {
      throw new Error(`获取系统信息失败: ${error.response?.data?.error || error.message}`)
    }
  }

  // 创建剧本
  async createScript(sceneDescription) {
    try {
      const response = await api.post('/create-script', {
        sceneDescription
      }, {
        timeout: 900000 // 15分钟超时，创建剧本包含图片生成需要更长时间
      })
      return response.data
    } catch (error) {
      throw new Error(`创建剧本失败: ${error.response?.data?.error || error.message}`)
    }
  }

  // 发送用户消息
  async sendMessage(message, round = 1) {
    try {
      const response = await api.post('/send-message', {
        message,
        round
      })
      return response.data
    } catch (error) {
      throw new Error(`发送消息失败: ${error.response?.data?.error || error.message}`)
    }
  }

  // 开始自动对话
  async startConversation(rounds = 5) {
    try {
      const response = await api.post('/start-conversation', {
        rounds
      })
      return response.data
    } catch (error) {
      throw new Error(`开始对话失败: ${error.response?.data?.error || error.message}`)
    }
  }

  // 获取下一个说话角色
  async getNextSpeaker(round = 1, situation = '') {
    try {
      const response = await api.post('/next-speaker', {
        round,
        situation
      })
      return response.data
    } catch (error) {
      throw new Error(`获取下一个说话角色失败: ${error.response?.data?.error || error.message}`)
    }
  }

  // 用户说话
  async userSpeak(message, round = 1, action = 'speak') {
    try {
      const response = await api.post('/user-speak', {
        message,
        round,
        action
      })
      return response.data
    } catch (error) {
      throw new Error(`用户发言失败: ${error.response?.data?.error || error.message}`)
    }
  }

  // AI角色说话
  async aiSpeak(speaker, round = 1, situation = '') {
    try {
      const response = await api.post('/ai-speak', {
        speaker,
        round,
        situation
      })
      return response.data
    } catch (error) {
      throw new Error(`AI角色发言失败: ${error.response?.data?.error || error.message}`)
    }
  }

  // 获取对话历史
  async getHistory() {
    try {
      const response = await api.get('/get-history')
      return response.data
    } catch (error) {
      throw new Error(`获取对话历史失败: ${error.response?.data?.error || error.message}`)
    }
  }

  // 清空对话历史
  async clearHistory() {
    try {
      const response = await api.post('/clear-history')
      return response.data
    } catch (error) {
      throw new Error(`清空历史失败: ${error.response?.data?.error || error.message}`)
    }
  }

  // 开始语音录音
  async startVoiceRecording() {
    try {
      const response = await api.post('/voice-start')
      return response.data
    } catch (error) {
      throw new Error(`开始录音失败: ${error.response?.data?.error || error.message}`)
    }
  }

  // 停止语音录音并识别
  async stopVoiceRecording(round = 1) {
    try {
      const response = await api.post('/voice-stop', {
        round
      })
      return response.data
    } catch (error) {
      throw new Error(`停止录音失败: ${error.response?.data?.error || error.message}`)
    }
  }

  // 获取语音录音状态
  async getVoiceStatus() {
    try {
      const response = await api.get('/voice-status')
      return response.data
    } catch (error) {
      throw new Error(`获取录音状态失败: ${error.response?.data?.error || error.message}`)
    }
  }

  // 获取用户对话选项
  async getDialogueOptions(round = 1) {
    try {
      const response = await api.post('/get-dialogue-options', {
        round
      })
      return response.data
    } catch (error) {
      throw new Error(`获取对话选项失败: ${error.response?.data?.error || error.message}`)
    }
  }

  // 选择对话选项
  async selectDialogue(selectedText, round = 1) {
    try {
      const response = await api.post('/select-dialogue', {
        selected_text: selectedText,
        round
      })
      return response.data
    } catch (error) {
      throw new Error(`选择对话失败: ${error.response?.data?.error || error.message}`)
    }
  }

  // 生成场景图片
  async generateSceneImage() {
    try {
      const response = await api.post('/generate-scene-image', {}, {
        timeout: 900000 // 15分钟超时，图片生成需要较长时间
      })
      return response.data
    } catch (error) {
      throw new Error(`生成场景图片失败: ${error.response?.data?.error || error.message}`)
    }
  }

  // 获取场景图片URL（已废弃，现在使用getLatestSceneImage）
  getSceneImageUrl() {
    // 构建基础URL
    const protocol = typeof window !== 'undefined' ? window.location.protocol : 'http:'
    const host = typeof window !== 'undefined' ? window.location.host : 'localhost:3000'
    return `${protocol}//${host}/scene-image`
  }

  // 获取基础URL
  getBaseURL() {
    // 图片文件通过后端提供，需要使用后端的端口
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol
      const hostname = window.location.hostname
      return `${protocol}//${hostname}:8900` // 后端端口
    }
    return 'http://localhost:8900' // 后端端口
  }

  // 获取最新场景图片信息
  async getLatestSceneImage() {
    try {
      const response = await api.get('/get-scene-image-url')
      return response.data
    } catch (error) {
      throw new Error(`获取最新场景图片失败: ${error.response?.data?.error || error.message}`)
    }
  }

  // 获取用户当前扮演的角色
  async getUserCharacter() {
    try {
      const response = await api.get('/get-user-character')
      return response.data
    } catch (error) {
      throw new Error(`获取用户角色失败: ${error.response?.data?.error || error.message}`)
    }
  }

  // 重置用户角色
  async resetUserCharacter() {
    try {
      const response = await api.post('/reset-user-character')
      return response.data
    } catch (error) {
      throw new Error(`重置用户角色失败: ${error.response?.data?.error || error.message}`)
    }
  }
}

export default new ApiService() 