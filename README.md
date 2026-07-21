# DifyCRM

面向飞书 + LangBot + Dify 的智能 CRM 业务系统。重点：获客营销闭环（渠道、活动、线索、评分、转客户、跟进、分析）。

---

## 先读：Clone 不能开箱即用

本仓库提供的是 **CRM 业务 API + SQL + Dify 工作流 DSL + 文档**。

完整「飞书里说人话用 CRM」还需要你**自行准备**：

| 组件 | 是否在本仓 | 说明 |
|------|------------|------|
| FastAPI + MySQL 脚本 | 是 | 本机可起 API |
| Dify（含 LLM 配置） | **否** | 需本地/自托管 Dify；并**手动导入** `dify/crm-main.yml` |
| LangBot + 飞书机器人 | **否** | 通常在独立基础设施部署中配置 |
| RAG 知识库接入主流程 | 规划能力 | 结构化数据始终以 MySQL 为准 |

导入 DSL 后，还需在 Dify 中配置「自然语言转指令」等节点所用的模型。

---

## 设计结论

- 关键业务数据落 MySQL（默认库名 `dify_crm`）。
- 飞书：聊天入口；Dify：NLU / 编排；**CRM API：业务核心**（避免多套真源）。
- RAG 只适合话术/FAQ 等非结构化资料；客户、线索、金额、状态等精确数据只查 MySQL。

## 项目结构

```text
DifyCRM/
  src/        FastAPI 业务服务
  sql/        建表与演示数据
  scripts/    初始化与启动脚本
  dify/       工作流 DSL 与集成说明
  docs/       入门地图、DEMO、PRD
```

## 文档

- [docs/CRM-入门与指令地图.md](docs/CRM-入门与指令地图.md) — 功能与指令
- [docs/DEMO.md](docs/DEMO.md) — 演示节奏
- [dify/README-DIFY-INTEGRATION.md](dify/README-DIFY-INTEGRATION.md) — Dify / LangBot 集成

## 最小可运行路径（仅 API）

### 1. 环境

- Python 3.10+
- 本机 MySQL（可用 `.env.example` 中的演示账号，按你环境修改）

```powershell
cd DifyCRM
copy .env.example .env
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
.\scripts\init_db.ps1
.\scripts\start_api.ps1
```

### 2. 验证

```powershell
Invoke-RestMethod http://127.0.0.1:5055/health
```

统一入口：

```http
POST http://127.0.0.1:5055/assistant/command
Content-Type: application/json

{
  "message": "/线索列表",
  "sender_id": "demo_sales"
}
```

Dify 若跑在 Docker 且需访问宿主机 API，使用：

```text
http://host.docker.internal:5055
```

### 3. 接入 Dify（完整体验）

1. 在 Dify 中**导入**本仓 `dify/crm-main.yml`（应用名建议 `crm_main`，结束节点字段 `summary`）。
2. 配置工作流中的 LLM 节点模型。
3. 将 HTTP 节点指向上述 API 的 `/assistant/command`。
4. LangBot 流水线指向该 Dify Workflow（Base URL 按你的 Dify 部署填写）。

详见 [dify/README-DIFY-INTEGRATION.md](dify/README-DIFY-INTEGRATION.md)。

## 配置（`.env.example`）

| 变量 | 含义 |
|------|------|
| `APP_HOST` / `APP_PORT` | API 监听 |
| `MYSQL_*` | 数据库连接 |
| `PUBLIC_API_BASE` | 容器内访问宿主机时的基址提示 |

**不要**把真实 `.env` 或云厂商 API Key 提交进 Git。

## License

MIT — 见 [LICENSE](LICENSE)。
