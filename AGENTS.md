# AGENT.md

项目知识库 / 上下文记录 (主要由 Agent 在工作中维护, 供后续步骤参考).

## 项目目标

在 RQData SDK 基础上, 为 23 个中国期货品种构建多 alpha 因子研究系统.
完整 workflow 见 `TODO.md`, 包含: Data Collection → Cleaning/Normalization → Alpha Gen → Signal Gen → Risk Scaling → Portfolio → Execution → Live Monitor → Risk Mgmt → Perf Attribution → Feedback Loop.

## Underlying Futures (23 个标的)

| 交易所 | 代码 | 品种 |
|---|---|---|
| DCE | C, M, Y, P, V, J, JD, I | 玉米, 豆粕, 豆油, 棕榈油, PVC, 焦炭, 鸡蛋, 铁矿石 |
| SHFE | CU, AL, AU, AG, RB, RU, NI, SN | 铜, 铝, 金, 银, 螺纹钢, 橡胶, 镍, 锡 |
| INE | SC | 原油 |
| CZCE | CF, SR, TA, MA, SA | 棉花, 白糖, PTA, 甲醇, 纯碱 |
| CFFEX | TF | 5年期国债 |

> RQData 文档索引: `doc/rqalpha-plus_api_*.md`, `doc/rqdata_python_*.md`. 调用前请先查本地文档, 不得凭经验推断.
> 不交易CFFEX上的股指类期货

---

## Step 1 - Data Collection (本步骤)

**已列出可用API及样例文件** 详见 `APIs.md`. 总共 102 个 CSV 样例文件已保存到 `data_samples/`.

