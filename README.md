# Crypto Funding Rate & OI Monitor (Bybit)

基于 GitHub Actions + Bark 的加密货币资金费率与未平仓合约（OI）监控系统。

**数据源已切换为 Bybit**（对美国 IP / GitHub Actions 更友好）。

重点监控 BTCUSDT / ETHUSDT 永续合约的资金费率极端值与 OI 快速变化，结合价格动作给出**高概率方向判断**（多头挤压 / 空头逼空），并通过 Bark 推送到 iPhone。

## 功能特点

- 量化规则引擎：资金费率 + OI 变化 + 价格变化共振打分
- 高/中高置信度过滤，冷却机制防刷屏
- 详细通知内容（价格、费率、OI 变化、判断理由、时间框架）
- 使用 Bybit 公开 API（无需 API Key）
- 零服务器成本，GitHub Actions 定时运行

## 快速部署

1. **添加 Secrets**  
   进入仓库 Settings → Secrets and variables → Actions → New repository secret  
   名称：`BARK_KEY`  
   值：从 Bark App 复制的设备 Key

2. **启用 Actions**  
   进入 Actions 页面，允许 workflow 运行。  
   也可以手动点击 `Critical Funding & OI Monitor` → Run workflow 测试。

3. **调整阈值**（可选）  
   编辑 `config.yaml` 中的阈值。

## 文件结构

```
crypto-monitor/
├── .github/workflows/critical.yml
├── src/
│   ├── main.py
│   ├── notifier.py
│   ├── state.py
│   ├── fetchers/
│   │   └── bybit.py          # Bybit 数据获取
│   └── rules/
│       └── derivatives.py
├── config.yaml
├── requirements.txt
└── README.md
```

## 注意事项

- 数据源：Bybit linear 永续（USDT 合约）
- 运行频率：每 15 分钟
- 推送条件：仅高/中高置信度信号，且有 60 分钟冷却
- 本系统仅做监控提醒，不构成投资建议

---
仅供个人学习与监控使用。
