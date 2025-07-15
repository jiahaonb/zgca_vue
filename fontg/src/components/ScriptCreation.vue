<template>
  <div class="script-creation">
    <el-card class="creation-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><Edit /></el-icon>
          <span>创建新剧本</span>
        </div>
      </template>

      <div class="creation-content">
        <!-- 说明区域 -->
        <el-alert
          title="欢迎来到ZGCA多智能体剧本编辑系统！"
          type="info"
          :closable="false"
          class="intro-alert"
        >
          <p>💡 您将作为主角参与剧本，系统会自动创建其他AI角色与您互动</p>
        </el-alert>

        <!-- 示例区域 -->
        <el-card class="examples-card" shadow="never">
          <template #header>
            <div class="examples-header">
              <el-icon><Lightbulb /></el-icon>
              <span>场景描述示例</span>
            </div>
          </template>
          
          <div class="examples-grid">
            <div 
              v-for="(example, index) in examples" 
              :key="index"
              class="example-item"
              @click="selectExample(example)"
            >
              <div class="example-icon">{{ example.icon }}</div>
              <div class="example-content">
                <h4>{{ example.title }}</h4>
                <p>{{ example.description }}</p>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 输入区域 -->
        <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
          <el-form-item label="场景描述" prop="sceneDescription">
            <el-input
              v-model="form.sceneDescription"
              type="textarea"
              :rows="6"
              placeholder="请详细描述您想要的剧本场景和设定..."
              show-word-limit
              maxlength="1000"
              class="scene-input"
            />
          </el-form-item>
        </el-form>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button type="default" @click="clearForm">
            <el-icon><Delete /></el-icon>
            清空内容
          </el-button>
          <el-button 
            type="primary" 
            @click="createScript" 
            :loading="creating"
            size="large"
          >
            <el-icon><Magic /></el-icon>
            {{ creating ? '创建中...' : '创建剧本' }}
          </el-button>
        </div>

        <!-- 创建结果 -->
        <el-card 
          v-if="creationResult" 
          class="result-card" 
          shadow="never"
        >
          <template #header>
            <div class="result-header">
              <el-icon><SuccessFilled /></el-icon>
              <span>剧本创建成功！</span>
            </div>
          </template>
          
          <div class="result-content">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="场景设定">
                {{ creationResult.data.scene }}
              </el-descriptions-item>
              <el-descriptions-item label="角色数量">
                {{ creationResult.data.characters_count }} 个角色
              </el-descriptions-item>
              <el-descriptions-item label="AI角色">
                <el-tag 
                  v-for="character in creationResult.data.characters" 
                  :key="character"
                  class="character-tag"
                  type="primary"
                >
                  🤖 {{ character }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
            
            <div class="result-actions">
              <el-button type="success" @click="goToChat">
                <el-icon><ChatDotRound /></el-icon>
                开始对话
              </el-button>
              <el-button type="info" @click="viewDetails" v-if="creationResult.data.characters_detail">
                <el-icon><View /></el-icon>
                查看角色详情
              </el-button>
            </div>
          </div>
        </el-card>
      </div>
    </el-card>

    <!-- 角色详情对话框 -->
    <el-dialog 
      v-model="detailsVisible" 
      title="角色详情" 
      width="60%"
      :before-close="handleCloseDetails"
    >
      <div v-if="creationResult && creationResult.data.characters_detail">
        <el-card 
          v-for="(character, index) in creationResult.data.characters_detail" 
          :key="index"
          class="character-detail-card"
          shadow="never"
        >
          <template #header>
            <div class="character-header">
              <span class="character-icon">
                {{ character.type === 'user' ? '👤' : '🤖' }}
              </span>
              <span class="character-name">{{ character.name }}</span>
              <el-tag :type="character.type === 'user' ? 'success' : 'primary'">
                {{ character.type === 'user' ? '用户主角' : 'AI角色' }}
              </el-tag>
            </div>
          </template>
          <p class="character-info">{{ character.info }}</p>
        </el-card>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, inject } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import apiService from '../services/api.js'

export default {
  name: 'ScriptCreation',
  setup() {
    const router = useRouter()
    const showLoading = inject('showLoading')
    const hideLoading = inject('hideLoading')

    const formRef = ref()
    const creating = ref(false)
    const detailsVisible = ref(false)
    
    const form = ref({
      sceneDescription: ''
    })

    const rules = {
      sceneDescription: [
        { required: true, message: '请输入场景描述', trigger: 'blur' },
        { min: 10, message: '场景描述至少需要10个字符', trigger: 'blur' }
      ]
    }

    const creationResult = ref(null)

    // 示例场景
    const examples = ref([
      {
        icon: '🏢',
        title: '现代都市',
        description: '现代都市背景，朋友们在咖啡厅讨论创业计划'
      },
      {
        icon: '⚔️',
        title: '古代武侠',
        description: '古代武侠世界，我在客栈遇到了神秘的江湖人士'
      },
      {
        icon: '🚀',
        title: '科幻未来',
        description: '科幻未来，我作为宇宙飞船的船员面临危机'
      },
      {
        icon: '🎓',
        title: '校园青春',
        description: '校园青春，我和同学在图书馆准备重要考试'
      },
      {
        icon: '🏰',
        title: '奇幻冒险',
        description: '魔法世界，我是一名冒险者在酒馆接受任务'
      },
      {
        icon: '🕵️',
        title: '悬疑推理',
        description: '推理悬疑，我是侦探在调查神秘案件'
      }
    ])

    // 选择示例
    const selectExample = (example) => {
      form.value.sceneDescription = example.description
      ElMessage.success(`已选择示例：${example.title}`)
    }

    // 清空表单
    const clearForm = () => {
      form.value.sceneDescription = ''
      creationResult.value = null
      ElMessage.info('已清空内容')
    }

    // 创建剧本
    const createScript = async () => {
      try {
        // 表单验证
        const valid = await formRef.value.validate()
        if (!valid) return

        creating.value = true
        showLoading('正在创建剧本，请稍候...')

        const result = await apiService.createScript(form.value.sceneDescription)
        
        if (result.success) {
          creationResult.value = result
          ElMessage.success('剧本创建成功！')
        } else {
          throw new Error(result.error || '创建失败')
        }
      } catch (error) {
        ElMessage.error(error.message || '创建剧本失败')
        console.error('创建剧本失败:', error)
      } finally {
        creating.value = false
        hideLoading()
      }
    }

    // 跳转到对话页面
    const goToChat = () => {
      router.push('/chat')
    }

    // 查看角色详情
    const viewDetails = () => {
      detailsVisible.value = true
    }

    // 关闭详情对话框
    const handleCloseDetails = () => {
      detailsVisible.value = false
    }

    return {
      formRef,
      creating,
      detailsVisible,
      form,
      rules,
      creationResult,
      examples,
      selectExample,
      clearForm,
      createScript,
      goToChat,
      viewDetails,
      handleCloseDetails
    }
  }
}
</script>

<style scoped>
.script-creation {
  max-width: 1000px;
  margin: 0 auto;
}

.creation-card {
  border-radius: 12px;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: bold;
  color: #409EFF;
}

.creation-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.intro-alert {
  border-radius: 8px;
}

.examples-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.examples-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
  color: #E6A23C;
}

.examples-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.example-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.example-item:hover {
  border-color: #409EFF;
  background: #f0f9ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.example-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.example-content h4 {
  margin: 0 0 4px 0;
  color: #303133;
  font-size: 14px;
}

.example-content p {
  margin: 0;
  color: #606266;
  font-size: 12px;
  line-height: 1.4;
}

.scene-input {
  border-radius: 8px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 8px;
}

.result-card {
  border: 2px solid #67c23a;
  border-radius: 8px;
  background: #f0f9ff;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
  color: #67c23a;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.character-tag {
  margin-right: 8px;
  margin-bottom: 4px;
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
}

.character-detail-card {
  margin-bottom: 16px;
}

.character-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.character-icon {
  font-size: 24px;
}

.character-name {
  font-weight: bold;
  font-size: 16px;
  flex: 1;
}

.character-info {
  margin: 0;
  line-height: 1.6;
  color: #606266;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .examples-grid {
    grid-template-columns: 1fr;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .result-actions {
    flex-direction: column;
  }
}
</style> 