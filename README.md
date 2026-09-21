# Crypto Funding Rate & OI Monitor

基于 GitHub Actions + Bark 的加密货币资金费率与未平仓合约（OI）监控系统。

重点监控 BTCUSDT / ETHUSDT 永续合约的资金费率极端值与 OI 快速变化，结合价格动作给出**高概率方向判断**（多头挤压 / 空头逼空），并通过 Bark 推送到 iPhone。

## 功能特点

- 量化规则引擎：资金费率 + OI 变化 + 价格变化共振打分
- 高/中高置信度过滤，冷却机制防刷屏
- 详细通知内容（价格、费率、OI 变化、判断理由、时间框架）
- 完全基于免费公开 API（Binance Futures）
- 零服务器成本，GitHub Actions 定时运行

## 快速部署

1. **添加 Secrets**  
   进入仓库 Settings → Secrets and variables → Actions → New repository secret  
   名称：`BARK_KEY`  
   值：从 Bark App 复制的设备 Key（形如 `xxxxxxxx`）

2. **启用 Actions**  
   进入 Actions 页面，允许 workflow 运行。  
   也可以手动点击 `Critical Funding & OI Monitor` → Run workflow 测试。

3. **调整阈值**（可选）  
   编辑 `config.yaml` 中的阈值，使其更激进或更保守。

## 文件结构

```
crypto-monitor/
├── .github/workflows/critical.yml   # 定时任务（每15分钟）
├── src/
│   ├── main.py                      # 主入口
│   ├── notifier.py                  # Bark 推送
│   ├── state.py                     # 状态与冷却
│   ├── fetchers/
│   │   └── binance.py               # Binance 数据获取
│   └── rules/
│       └── derivatives.py           # 核心量化判断规则
├── config.yaml                      # 阈值与配置
├── requirements.txt
└── README.md
```

## 通知示例

```
【高概率短期回调】BTCUSDT
置信度: 高 | 得分: 4.5
时间框架: 1-6小时

当前价格: $84,250.00
1h涨跌: +2.15% | 4h涨跌: +4.80%
资金费率(8h): +0.0950%
OI变化: 1h +6.20% | 4h +6.20%
当前OI: 85,234 张

判断: 多头过热，易引发连环平仓
理由:
  • 资金费率极端正值 ≥ 0.08%
  • OI 快速大幅堆积
  • 价格加速上涨确认过热

仅供参考，不构成投资建议。
```

## 本地测试

```bash
export BARK_KEY=你的key
pip install -r requirements.txt
python -m src.main
```

## 注意事项

- GitHub Actions 的 cron 是 best-effort，高峰时段可能有延迟。
- 当前 OI 4h 变化使用简化逻辑（与上次运行对比），后续可扩展为真正的多周期历史存储。
- 本系统仅做监控提醒，不构成任何投资建议。
- **重要**：Binance Futures API 在部分地区（含美国 IP）可能被限制。如果运行失败提示网络错误，请告知，我可以帮你切换到 Bybit / OKX 或其他可用数据源。
- 请遵守 API 使用规范，避免过于频繁请求。

## 后续可扩展方向

- 增加多交易所对比（Bybit / OKX）
- 真正 4h / 24h OI 历史对比
- 加入爆仓数据、多空比
- DefiLlama TVL 模块
- 动态分位数阈值

---
仅供个人学习与监控使用。
