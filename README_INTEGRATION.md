# 🚀 Euraxess 一体化爬虫应用

## 📖 功能说明

这是一个集成了**定时爬虫**和**Web 数据展示**的一体化 Docker 应用：

✅ **自动定时爬取**: 每天世界时间（UTC）下午 6 点（18:00）自动运行  
✅ **实时 Web 界面**: 通过 Streamlit 提供数据筛选和可视化  
✅ **数据持久化**: 所有数据保存在本地`output/`目录  
✅ **一个镜像**: 无需管理多个容器，简单高效

## 🎯 快速开始

### 方法 1: Docker Compose (推荐)

```bash
# 启动一体化服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方法 2: 单个 Docker 命令

```bash
# 启动完整服务
docker run -d -p 8501:8501 -v "${PWD}/output:/app/output" --name euraxess euraxess-scraper

# 查看日志
docker logs -f euraxess

# 停止服务
docker stop euraxess && docker rm euraxess
```

### 方法 3: 使用管理脚本 (Windows)

```powershell
# 启动服务
.\manage-scheduler.ps1 start

# 查看状态
.\manage-scheduler.ps1 status

# 查看定时信息
.\manage-scheduler.ps1 schedule

# 立即运行爬虫
.\manage-scheduler.ps1 run-now
```

## 🌐 访问应用

启动后，在浏览器中打开：**http://localhost:8501**

## ⏰ 定时任务详情

- **运行时间**: 每天 UTC 18:00 (世界时间下午 6 点)
- **对应时区**:
  - 北京时间: 次日 02:00
  - 纽约时间: 14:00 (夏令时) / 13:00 (标准时间)
  - 伦敦时间: 19:00 (夏令时) / 18:00 (标准时间)

## 📁 文件结构

```
euraxess_scraper/
├── 🐳 docker-compose.yml    # Docker Compose配置
├── 🐳 Dockerfile           # 一体化镜像配置
├── 📋 requirements.txt     # Python依赖
├── 🕷️ euraxess/            # Scrapy爬虫代码
├── 📊 app.py              # Streamlit应用
├── 📂 output/             # 数据输出目录
└── 🔧 manage-scheduler.ps1 # Windows管理脚本
```

## 🔧 高级用法

### 仅运行特定功能

```bash
# 仅运行爬虫一次
docker run --rm -v "${PWD}/output:/app/output" euraxess-scraper scrape

# 仅运行Web界面
docker run -p 8501:8501 -v "${PWD}/output:/app/output" euraxess-scraper streamlit

# 仅运行定时任务
docker run -v "${PWD}/output:/app/output" euraxess-scraper scheduler
```

### 自定义定时

如需修改定时设置，编辑 Dockerfile 中的 cron 配置：

```bash
# 当前: 每天18:00 UTC
# 修改为每天12:00 UTC: 将 "0 18" 改为 "0 12"
```

## 🛠️ 故障排除

### 端口冲突

如果 8501 端口被占用，使用其他端口：

```bash
docker run -p 8502:8501 -v "${PWD}/output:/app/output" euraxess-scraper
# 然后访问 http://localhost:8502
```

### 查看定时任务日志

```bash
docker exec -it euraxess tail -f /var/log/cron.log
```

### 重新构建镜像

```bash
docker build -t euraxess-scraper . --no-cache
```

## 📈 数据说明

- **数据来源**: Euraxess 欧洲科研职位网站
- **更新频率**: 每天自动更新
- **数据格式**: CSV 文件存储在`output/jobs.csv`
- **历史数据**: 保留每日爬取的历史文件

## 🎉 享受使用！

现在你有了一个完全自动化的职位数据收集和分析系统！

- 🔄 无需手动操作，每天自动更新数据
- 📊 随时通过 Web 界面查看和筛选数据
- 🐳 Docker 容器化，部署简单，环境一致
- 💾 数据持久化，重启不丢失
