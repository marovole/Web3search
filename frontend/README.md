# Web3 AI Search Engine - Frontend

基于React + TypeScript + Vite的现代化前端应用，提供ChatGPT风格的对话式加密货币研究体验。

## ✨ 功能特性

- 🚀 **双模式AI分析**
  - Quick Chat：3秒快速问答
  - Deep Research：30秒深度研究报告

- 💬 **现代化对话界面**
  - 实时SSE流式输出
  - Markdown渲染（表格、代码、图表）
  - 自动滚动、多阶段加载动画

- 📊 **专业报告展示**
  - 目录导航（TOC）
  - 章节锚点跳转
  - 打印友好样式

- 📤 **便捷导出功能**
  - 下载Markdown文件
  - 打印PDF报告
  - 复制分享链接

- 📱 **响应式设计**
  - 桌面端、平板、移动端全适配
  - Tailwind CSS定制主题

## 🛠️ 技术栈

- **框架**: React 18 + TypeScript 5
- **构建工具**: Vite 5 (快速HMR)
- **样式**: Tailwind CSS 3 + @tailwindcss/typography
- **路由**: React Router v6
- **Markdown**: react-markdown + remark-gfm
- **代码高亮**: react-syntax-highlighter
- **HTTP**: Axios (拦截器 + 重试)
- **图表**: Recharts (可选)

## 📦 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

复制环境变量模板并根据需要修改：

```bash
cp .env.example .env.local
```

编辑`.env.local`：

```bash
# 后端API地址
VITE_API_BASE_URL=http://localhost:8000

# 生产环境（可选）
# VITE_API_BASE_URL=https://web3search-api.onrender.com
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000)

### 4. 构建生产版本

```bash
npm run build
```

构建产物输出到`dist/`目录。

### 5. 预览生产版本

```bash
npm run preview
```

## 📁 项目结构

```
src/
├── components/          # React组件
│   ├── Chat/           # 聊天相关组件
│   │   ├── ChatInterface.tsx    # 主对话界面
│   │   ├── ModeSwitch.tsx      # 模式切换器
│   │   ├── MessageBubble.tsx   # 消息气泡
│   │   ├── MessageList.tsx     # 消息列表
│   │   └── InputBox.tsx        # 输入框
│   ├── Report/         # 报告相关组件
│   │   ├── ReportViewer.tsx    # 报告查看器
│   │   └── ExportButton.tsx    # 导出按钮
│   └── Shared/         # 共享组件
│       └── LoadingAnimation.tsx # 加载动画
├── pages/              # 页面组件
│   ├── ChatPage.tsx            # 聊天页面
│   └── SharedReportPage.tsx    # 分享报告页面
├── services/           # API服务层
│   └── api.ts                  # API封装
├── types/              # TypeScript类型定义
│   └── index.ts
├── App.tsx             # 根组件
├── main.tsx            # 入口文件
└── index.css           # 全局样式
```

## 🎨 样式系统

### Tailwind CSS主题

在`tailwind.config.js`中定义的自定义颜色：

```javascript
colors: {
  primary: '#2E86DE',   // 主色调（蓝色）
  secondary: '#576574', // 次色调（灰色）
  success: '#27AE60',   // 成功（绿色）
  danger: '#E74C3C',    // 危险（红色）
  warning: '#F39C12',   // 警告（橙色）
  info: '#17A2B8',      // 信息（青色）
}
```

### 自定义CSS类

在`index.css`中定义的工具类：

- `.btn-primary` - 主按钮样式
- `.btn-secondary` - 次按钮样式
- `.btn-danger` - 危险按钮样式
- `.card` - 卡片样式
- `.input` - 输入框样式
- `.message-user` - 用户消息气泡
- `.message-assistant` - AI消息气泡
- `.custom-scrollbar` - 自定义滚动条

## 🔌 API集成

前端通过`src/services/api.ts`与后端通信：

| API端点 | 方法 | 说明 |
|---------|------|------|
| `/api/v1/chat/quick-chat` | POST | Quick Chat模式 |
| `/api/v1/chat/deep-research/stream` | SSE | Deep Research流式输出 |
| `/api/v1/reports/{id}` | GET | 获取报告详情 |
| `/api/v1/reports/{id}/share` | POST | 创建分享链接 |
| `/api/v1/reports/shared/{token}` | GET | 获取分享报告 |

### SSE流式接收示例

```typescript
const eventSource = new EventSource('/api/v1/chat/deep-research/stream?query=BTC');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.content); // 逐步接收内容
};
```

## 🧪 开发指南

### 添加新组件

1. 在`src/components/`创建组件文件
2. 定义TypeScript接口（Props类型）
3. 使用Tailwind CSS编写样式
4. 导出组件

```typescript
interface MyComponentProps {
  title: string;
  onClick: () => void;
}

const MyComponent: React.FC<MyComponentProps> = ({ title, onClick }) => {
  return (
    <button onClick={onClick} className="btn-primary">
      {title}
    </button>
  );
};

export default MyComponent;
```

### 调用后端API

```typescript
import { quickChat } from '@/services/api';

const response = await quickChat({
  query: '分析BTC',
  conversation_id: 'abc123',
});

console.log(response.answer);
```

### TypeScript类型检查

```bash
# 检查类型错误
npm run build  # 或直接在IDE中查看
```

## 🚀 部署

### Vercel部署（推荐）

1. 在Vercel导入GitHub仓库
2. 配置环境变量：`VITE_API_BASE_URL`
3. 构建命令：`npm run build`
4. 输出目录：`dist`
5. 点击部署

### 手动部署

```bash
# 1. 构建
npm run build

# 2. 上传dist/目录到静态托管服务
#    - Vercel / Netlify / Cloudflare Pages
#    - GitHub Pages
#    - Nginx / Apache
```

### 环境变量配置

生产环境需要配置：

```bash
VITE_API_BASE_URL=https://your-backend-api.com
```

## 🐛 常见问题

### 1. API请求失败（CORS错误）

确保后端配置了正确的CORS头：

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. SSE连接中断

- 检查后端是否正确发送`Content-Type: text/event-stream`
- 确认EventSource URL是否正确
- 查看浏览器控制台是否有网络错误

### 3. Markdown渲染异常

- 确保安装了`remark-gfm`插件（支持表格）
- 检查Base64图片格式是否正确：`data:image/png;base64,...`

### 4. 构建失败

```bash
# 清除缓存重试
rm -rf node_modules dist
npm install
npm run build
```

## 📝 待办事项

- [ ] 添加用户认证（JWT Token）
- [ ] 实现暗黑模式切换
- [ ] 添加国际化（i18n）支持
- [ ] 集成Recharts交互式图表
- [ ] 添加单元测试（Vitest）
- [ ] 性能优化（懒加载、代码分割）

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

**技术支持**: [GitHub Issues](https://github.com/your-repo/issues)
