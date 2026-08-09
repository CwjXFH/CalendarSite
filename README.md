# calendarsite

公开日历站点：同时展示阳历 / 阴历，界面简洁，支持 Web 与移动端。

## 业务需求

1. 这是一个日历站点
2. 界面上显示阳历和阴历两种日期信息
3. 界面上默认显示当前年、月表，当前日期用红框框起来
4. 非工作日的周末用浅红色背景
5. 法定节假日用稍微深色些的红色背景
6. 用户可以点击年、月、日来选择日期
7. 日历表格上要显示传统节假日及二十四节气信息
8. 界面保持简洁风格
9. 年份选择范围从 1900～未来 3 年
10. 支持 web 和移动端

## 技术栈

| 层 | 选型 |
|----|------|
| 前端 | 最新稳定 React + TypeScript + Vite + Ant Design |
| 后端 | 最新稳定 FastAPI + Python，uv 管理依赖 |
| 数据 | SQLite3（仅法定假日 / 调休） |
| 农历节气 | 算法计算（lunar-python），不入库 |
| 部署 | 云服务器 + Docker Compose + Nginx |
| 版本控制 | Git |

前端原则：代码简洁、少抽象，尽量用 antd，降低维护成本。

## 架构原则

1. **厚后端、薄前端**：日历数据由 API 组装；前端只负责展示与配色。
2. **前后端零实现耦合**：唯一契约是稳定的 HTTP/JSON；技术栈可独立演进。
3. **OpenAPI 为契约源**，接口带版本前缀 `/api/v1`。
4. **展示规则在前端**（红框、背景色）；**文案与业务标记在后端**。

```text
浏览器 → Nginx（静态 + 限流 + 反代）
           ├─ /        → 前端静态资源
           └─ /api/v1  → FastAPI → SQLite / 农历算法
```

## 稳定 API（v1）

| 接口 | 作用 |
|------|------|
| `GET /api/v1/health` | 健康检查 |
| `GET /api/v1/meta` | `minYear` / `maxYear` |
| `GET /api/v1/calendar?year=&month=` | 月视图格子数据 |

月响应字段：

- `lunarYearMonth`：农历年月（如 `丙午年六月`），供页头展示

格子字段（语义冻结）：

- `date`：`YYYY-MM-DD`
- `day`：公历日
- `lunarText`：农历文案
- `lunarYearMonth`：该日农历年月（如 `丙午年六月`）
- `festival`：传统节日（无则为 `null`）
- `solarTerm`：二十四节气（无则为 `null`）
- `isWeekend`：是否自然周末
- `isLegalHoliday`：是否法定节假日
- `isMakeupWorkday`：是否调休补班
- `isCurrentMonth`：是否属于查询月

约定：

- 兼容变更可新增字段；删改字段或改语义必须上 `/api/v2`。
- 统一错误体：`{ "code": "...", "message": "..." }`。
- 前端不感知 SQLite / 算法库；后端不感知 React / antd。

## 防刷

- Nginx：按 IP 限流。
- FastAPI：应用层限流，超限返回 `429`，`code` 为 `RATE_LIMITED`。
- 参数严格校验；按月结果可短时缓存。
- 不对外暴露后端端口；不在前端藏密钥。

## 职责划分

- **SQLite**：法定假日、调休上班日。
- **算法库**：农历、节气、传统节日文案。
- **React + antd**：年月选择、月历网格、选中态、周末/假日样式、响应式。

## 本地开发

### 后端

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 容器部署

```bash
docker compose up --build -d
```

## 目录结构

```text
calendarsite/
├── backend/          # FastAPI + uv + SQLite + lunar-python
├── frontend/         # React + Vite + TypeScript + Ant Design
├── docker-compose.yml
└── README.md
```

## 说明

- Python 版本：3.14（与本机 uv 环境一致）
- 农历库：`lunar-python`（`sxtwl` 在 3.14 上无法编译，故改用纯 Python 实现）
- 法定假日种子数据覆盖 2024–2026；未公布年份以国务院文件为准更新 SQLite
