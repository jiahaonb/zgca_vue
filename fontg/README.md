# ZGCA多智能体剧本编辑系统 - Vue前端

## 项目介绍

这是ZGCA多智能体剧本编辑系统的Vue 3前端界面，提供了用户友好的Web界面来与后端API交互。

## 功能特性

### 🎭 剧本创建

- 支持自定义场景描述
- 提供多种场景模板
- 自动生成AI角色
- 实时显示创建结果

### 💬 智能对话

- 实时聊天界面
- 支持用户与AI角色互动
- 智能角色调度
- 对话历史记录
- 自动对话功能

### 📊 系统监控

- 实时系统状态监控
- API使用情况统计
- 连接状态检测
- 系统日志查看

## 技术栈

- **Vue 3** - 渐进式JavaScript框架
- **Element Plus** - Vue 3 UI组件库
- **Vue Router** - Vue官方路由管理器
- **Axios** - HTTP客户端
- **Vite** - 现代前端构建工具

## 项目结构

```
fontg/
├── public/              # 静态资源
├── src/                 # 源代码
│   ├── components/      # Vue组件
│   │   ├── ScriptCreation.vue    # 剧本创建页面
│   │   ├── ChatInterface.vue     # 对话界面
│   │   └── SystemStatus.vue      # 系统状态页面
│   ├── services/        # API服务
│   │   └── api.js       # API封装
│   ├── App.vue          # 根组件
│   └── main.js          # 入口文件
├── index.html           # HTML模板
├── package.json         # 项目配置
├── vite.config.js       # Vite配置
└── README.md           # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
cd fontg
npm install
```

### 2. 启动后端服务

确保后端服务正在运行在 `http://127.0.0.1:8900`

```bash
cd ../backg
python electron_bridge.py
```

### 3. 启动前端开发服务器

```bash
npm run dev
```

前端将在 `http://localhost:3000` 启动

### 4. 构建生产版本

```bash
npm run build
```

构建文件将输出到 `dist/` 目录

## API配置

前端通过Vite代理配置自动将 `/api` 路径代理到后端服务：

```javascript
// vite.config.js
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8900',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
```

## 主要API端点

| 端点                   | 方法 | 说明             |
| ---------------------- | ---- | ---------------- |
| `/api/status`        | GET  | 获取系统状态     |
| `/api/create-script` | POST | 创建剧本         |
| `/api/send-message`  | POST | 发送消息         |
| `/api/get-history`   | GET  | 获取对话历史     |
| `/api/clear-history` | POST | 清空历史         |
| `/api/next-speaker`  | POST | 获取下一个发言者 |
| `/api/user-speak`    | POST | 用户发言         |
| `/api/ai-speak`      | POST | AI角色发言       |

## 使用说明

### 1. 创建剧本

1. 访问"创建剧本"页面
2. 选择示例场景或输入自定义描述
3. 点击"创建剧本"按钮
4. 查看生成的角色信息
5. 点击"开始对话"进入聊天界面

### 2. 进行对话

1. 在对话界面输入您的台词
2. 系统会自动调度AI角色回复
3. 支持跳过发言功能
4. 可以启动自动对话模式

### 3. 监控系统

1. 访问"系统状态"页面
2. 查看连接状态和系统信息
3. 监控API使用情况
4. 管理系统日志

## 开发说明

### 组件说明

#### ScriptCreation.vue

- 剧本创建表单
- 场景示例选择
- 创建结果展示
- 角色详情对话框

#### ChatInterface.vue

- 对话消息显示
- 消息输入框
- 角色信息面板
- 自动对话功能

#### SystemStatus.vue

- 系统状态监控
- API使用统计
- 系统日志显示
- 管理操作面板

#### api.js

- 封装所有API调用
- 请求/响应拦截器
- 错误处理机制

### 样式设计

- 使用Element Plus组件库
- 响应式设计，支持移动端
- 现代化UI设计
- 渐变色彩搭配

## 故障排除

### 常见问题

1. **连接失败**

   - 检查后端服务是否启动
   - 确认端口8900是否被占用
   - 查看控制台错误信息
2. **API调用失败**

   - 检查网络连接
   - 确认API密钥配置
   - 查看后端日志
3. **页面无法加载**

   - 清除浏览器缓存
   - 检查JavaScript控制台错误
   - 重新安装依赖

### 日志调试

前端会在浏览器控制台输出详细的API请求和响应日志，方便调试。

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

## 许可证

MIT License

## 联系方式

如有问题请提交Issue或联系开发团队。
