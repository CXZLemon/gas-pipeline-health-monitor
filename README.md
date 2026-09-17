# Gas Pipeline Health Monitor

一个面向天然气管道运行数据的轻量级异常检测与可视化项目。项目从压力、流量和温度时序数据出发，自动构造运行特征，使用 Isolation Forest 识别疑似泄漏、堵塞或传感器漂移，并在 Streamlit 页面中展示风险点。

> 适合用途：数据分析 / Python 开发 / 工业智能 / 能源数字化岗位的入门项目与作品集项目。

## 项目亮点

- **无需真实敏感数据**：内置可复现的合成数据生成器，并保留注入异常标签用于离线验证。
- **完整数据闭环**：数据生成或上传 → 清洗校验 → 特征工程 → 模型检测 → 可视化 → CSV 导出。
- **容易解释**：Isolation Forest 不依赖异常标签，符合工业现场异常样本少的常见情况。
- **具备工程结构**：业务逻辑与页面解耦，包含数据库存储、单元测试和 GitHub Actions。
- **可逐步扩展**：可替换成真实 SCADA 数据，也可升级为预测模型、在线告警或 MySQL 服务。

## 效果与功能

应用页面支持：

1. 生成内置管道样例，或上传自己的 CSV 数据。
2. 选择管段、异常比例和滚动窗口。
3. 查看压力、流量、温度、压降和风险分数。
4. 标记模型判断的异常时刻并展示高风险记录。
5. 若使用合成数据，同时计算 Precision、Recall 和 F1。
6. 下载包含特征、异常标签与风险分数的分析结果。

## 技术路线

```mermaid
flowchart LR
    A[合成数据 / CSV] --> B[数据校验与清洗]
    B --> C[时序特征工程]
    C --> D[标准化]
    D --> E[Isolation Forest]
    E --> F[异常标签与风险分数]
    F --> G[Streamlit + Plotly]
    F --> H[SQLite / MySQL]
```

核心特征包括入口压力、出口压力、质量流量、温度、压降、压降比、流量变化率、滚动均值、滚动标准差和时间周期编码。

## 技术栈

- Python 3.10+
- Pandas / NumPy：数据清洗、时序特征与统计计算
- scikit-learn：StandardScaler 与 Isolation Forest
- Streamlit / Plotly：交互式数据应用和可视化
- SQLAlchemy：SQLite 默认存储，并兼容 MySQL 连接串
- pytest：核心模块自动化测试
- GitHub Actions：提交后自动执行测试

## 快速开始

### 1. 创建环境并安装依赖

```bash
python -m venv .venv
```

Windows：

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS / Linux：

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 启动可视化页面

```bash
streamlit run streamlit_app.py
```

浏览器打开 `http://localhost:8501`。首次使用可直接选择“内置合成数据”，不需要准备数据文件。

### 3. 运行命令行演示

```bash
python scripts/run_demo.py
```

程序会在 `outputs/` 中写出检测结果，并将原始遥测数据保存到本地 SQLite 数据库。

### 4. 运行测试

```bash
pytest -q
```

## 上传数据格式

CSV 至少包含以下字段：

```text
timestamp,component_id,inlet_pressure,outlet_pressure,flow_rate,temperature
```

- `timestamp`：可被 Pandas 解析的时间
- `component_id`：管段或设备编号
- 压力单位建议统一为 MPa
- 流量单位建议统一为 kg/s
- 温度单位建议统一为摄氏度

如果数据中存在 `is_injected_anomaly` 列，页面会把它当作真实标签计算离线指标；真实业务数据通常没有该列，此时只展示无监督检测结果。

## 数据库存储

默认连接本地 SQLite：

```text
sqlite:///data/pipeline_monitor.db
```

也可以通过环境变量切换到 MySQL：

```powershell
$env:DATABASE_URL="mysql+pymysql://user:password@localhost:3306/gas_monitor?charset=utf8mb4"
python scripts/run_demo.py
```

数据库账号密码不要写入代码或提交到 GitHub，生产环境应使用环境变量或密钥管理服务。

## 项目结构

```text
gas-pipeline-health-monitor/
├── .github/workflows/ci.yml       # 自动测试
├── docs/
│   ├── INTERVIEW_GUIDE.md         # 简历写法与面试问答
│   └── PROJECT_GUIDE.md           # 原理与学习路线
├── scripts/run_demo.py            # 命令行完整流程
├── src/gas_monitor/
│   ├── data.py                    # 合成数据与数据校验
│   ├── detector.py                # 异常检测模型
│   ├── features.py                # 特征工程
│   └── storage.py                 # 数据库存储
├── tests/                         # 单元测试
├── streamlit_app.py               # 可视化入口
├── pyproject.toml
└── requirements.txt
```

## 模型为什么选择 Isolation Forest

工业异常通常数量少、标签不完整。Isolation Forest 通过随机切分特征空间来隔离样本，异常点通常更容易被少量切分单独隔离，因此无需大量人工标签即可给出异常排序。它训练速度快、参数少，适合作为入门基线。

模型输出是“疑似异常”，不是泄漏诊断结论。工程上线前必须结合设备阈值、工艺规则、检修记录与人工复核，并通过按时间划分的历史数据评估误报和漏报。

## 后续迭代方向

- 接入真实 SCADA 或历史数据库，增加缺失值与坏点处理。
- 使用滑动时间窗构造监督学习样本，对比 XGBoost、LSTM 与自编码器。
- 引入 FastAPI 提供推理接口，并加入告警冷却、确认和闭环记录。
- 用 Docker Compose 启动应用与 MySQL，比较索引前后的查询性能。
- 将物理规则加入风险分数，例如压力突降与流量不平衡联合判定。

## License

MIT

