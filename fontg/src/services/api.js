import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
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
}

export default new ApiService() 