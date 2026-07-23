# meng - AI 简历优化器

一个简单易用的 AI 简历优化工具。上传你的 PDF 简历，AI 会在 3 分钟内给出：

- 简历评分
- 主要问题
- 具体修改建议
- 优化后的简历内容

## 适合谁用

- 应届毕业生
- 工作 1-5 年想跳槽的人
- 转行/跨行业求职者

## 快速开始

### 1. 克隆/下载项目

项目位置：`D:/meng`

### 2. 安装依赖

```bash
cd /d/meng
pip install -r requirements.txt
```

### 3. 配置 API Key

复制 `.env.example` 为 `.env`，填入你的 DeepSeek API Key：

```bash
cp .env.example .env
```

编辑 `.env`：

```env
DEEPSEEK_API_KEY=your_api_key_here
```

> 没有 API Key？去 [DeepSeek 开放平台](https://platform.deepseek.com/) 注册，新用户有免费额度。

### 4. 运行项目

```bash
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`

## 文件结构

```
meng/
├── app.py                  # Streamlit 前端主程序
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量示例
├── README.md               # 项目说明
├── docs/
│   └── PRD.md              # 产品需求文档
├── src/
│   ├── __init__.py
│   ├── resume_parser.py    # PDF 简历解析
│   └── resume_analyzer.py  # AI 分析模块
├── tests/                  # 测试文件
└── examples/               # 示例简历
```

## 使用说明

1. 打开网页后，在左侧输入你的 DeepSeek API Key（也可以提前写在 `.env` 里）。
2. 上传你的 PDF 简历。
3. 点击「开始分析」。
4. 查看评分、问题和优化后的简历。
5. 复制优化结果，粘贴到你的简历里。

## 后续计划

- [ ] 支持岗位 JD 对比优化
- [ ] 支持 Word/PDF 导出
- [ ] 增加用户系统和支付
- [ ] 行业/岗位模板库
- [ ] 面试模拟功能

## 许可证

MIT
