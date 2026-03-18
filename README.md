# 山西省 WebGIS 平台

## 项目简介

基于 FastAPI + Vue 3 + OpenLayers 的山西省矿井 WebGIS 数据分析平台，支持：
- 栅格数据上传与 COG（云优化 GeoTIFF）预处理
- 通过 TiTiler 动态切片服务在线浏览栅格数据
- 矿井点位 Excel 批量导入与地图展示
- 自动生成 PDF 数据分析报告
- 异步任务队列（Celery + Redis）

## 环境要求

- **Docker Desktop**（推荐最新版；Windows 用户请启用 WSL2 后端，macOS/Linux 用户直接安装即可）
- Git

## 快速启动（本地部署）

```bash
# 1. 克隆仓库
git clone <your-repo-url>
cd shanxi

# 2. 复制环境变量文件
cp .env.example .env
```

用文本编辑器打开 `.env`，按需修改以下关键配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `POSTGRES_PASSWORD` | 数据库密码 | `shanxi123` |
| `SECRET_KEY` | JWT 签名密钥（生产环境请务必更换） | `change-me-in-production` |
| `VITE_TIANDITU_TOKEN` | 天地图 API Token（[申请地址](https://uumaps.tianditu.gov.cn/)，留空时前端代码自动使用内置演示 token） | 空 |
| `VITE_TITILER_URL` | TiTiler 服务地址 | `http://localhost:8080` |

```bash
# 3. 一键构建并启动所有服务
docker compose up -d --build
```

> 首次启动需要拉取镜像和编译前端，约需 **3–5 分钟**。  
> 可通过 `docker compose logs -f` 实时查看进度。

```bash
# 查看各服务运行状态（全部 healthy 即就绪）
docker compose ps
```

## 访问地址

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost |
| 后端 API | http://localhost:8000 |
| Swagger 文档 | http://localhost:8000/docs |
| TiTiler 服务 | http://localhost:8080 |
| Redis | localhost:6379 |
| PostgreSQL | localhost:5432 |

## 停止 / 清理

```bash
# 停止所有容器（保留数据卷）
docker compose down

# 停止并删除所有数据（包括数据库）
docker compose down -v
```

## 端到端演示流程

1. **上传栅格** → 点击「上传」标签页 → 选择 .tif 文件上传
2. **预处理** → 上传完成后点击「启动预处理」→ 等待 COG 转换完成（状态变为 SUCCESS）
3. **加载图层** → 切换到「图层」标签页 → 点击「加载到地图」
4. **导入井点** → 切换到「井点」标签页 → 导入包含 name/lon/lat 列的 Excel 文件
5. **显示井点** → 点击「显示井点」按钮，井点将显示在地图上
6. **生成报告** → 切换到「报告」标签页 → 选择关联栅格 → 点击「生成报告」→ 下载 PDF

## 项目结构

```
shanxi/
├── docker-compose.yml      # 一键启动配置
├── .env.example            # 环境变量模板
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── api/           # API 路由
│   │   ├── models/        # SQLAlchemy 数据模型
│   │   ├── schemas/       # Pydantic 模式
│   │   ├── services/      # 业务逻辑服务
│   │   └── tasks/         # Celery 异步任务
│   └── alembic/           # 数据库迁移
├── frontend/               # Vue 3 前端
│   └── src/
│       ├── components/    # Vue 组件
│       ├── api/           # API 调用封装
│       ├── store/         # Pinia 状态管理
│       └── pages/         # 页面组件
├── db/                    # 数据库初始化脚本
├── data/                  # 数据目录（已挂载到容器）
│   ├── raw/               # 原始上传文件
│   ├── processed/         # COG 处理后文件
│   └── reports/           # 生成的 PDF 报告
└── ai-service/            # AI 服务（待实现）
```

## 未来扩展

- **融合模块** (`/api/fusion/jobs`): 多源数据融合分析
- **SAM2 智能识别** (`/api/ai/detect`): 基于 SAM2 的地物识别
- **热力图分析** (`/api/analytics/heatgrid`): 矿井分布热力图
