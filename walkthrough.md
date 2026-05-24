# Walkthrough — Historical Research Pipeline

## Summary

Extended the StockResearch dashboard into a full behavioral finance research platform. Added persistent storage, automated data collection, forward return computation, correlation analysis, and event study capabilities.

## What Was Built

### New Files (16)

| File | Purpose |
|------|---------|
| [database/\_\_init\_\_.py](file:///d:/StockResearch/backend/database/__init__.py) | Database package exports |
| [database/models.py](file:///d:/StockResearch/backend/database/models.py) | SQLAlchemy ORM models (3 tables) |
| [database/database.py](file:///d:/StockResearch/backend/database/database.py) | Engine, session, init_db |
| [services/data_quality.py](file:///d:/StockResearch/backend/services/data_quality.py) | Trading calendar, timezone, dedup |
| [services/research_service.py](file:///d:/StockResearch/backend/services/research_service.py) | Forward/abnormal return computation |
| [scripts/\_\_init\_\_.py](file:///d:/StockResearch/backend/scripts/__init__.py) | Scripts package |
| [scripts/config.py](file:///d:/StockResearch/backend/scripts/config.py) | Symbols, benchmark, logging config |
| [scripts/collect_news.py](file:///d:/StockResearch/backend/scripts/collect_news.py) | News collection + FinBERT scoring |
| [scripts/collect_stock_data.py](file:///d:/StockResearch/backend/scripts/collect_stock_data.py) | OHLCV + indicator download |
| [scripts/build_research_dataset.py](file:///d:/StockResearch/backend/scripts/build_research_dataset.py) | Forward return builder |
| [scripts/run_daily_pipeline.py](file:///d:/StockResearch/backend/scripts/run_daily_pipeline.py) | Pipeline orchestrator |
| [scripts/scheduler_examples.md](file:///d:/StockResearch/backend/scripts/scheduler_examples.md) | Cron/Task Scheduler docs |
| [research/correlation_analysis.py](file:///d:/StockResearch/backend/research/correlation_analysis.py) | Correlation notebook |
| [research/event_study.py](file:///d:/StockResearch/backend/research/event_study.py) | Event study notebook |

### Modified Files (3)

| File | Changes |
|------|---------|
| [main.py](file:///d:/StockResearch/backend/main.py) | Added 3 research endpoints + DB init on startup |
| [requirements.txt](file:///d:/StockResearch/backend/requirements.txt) | Added sqlalchemy, scipy, statsmodels, matplotlib, plotly, jupytext |
| [PROGRESS.md](file:///d:/StockResearch/PROGRESS.md) | Full Phase 2 documentation |

### Updated Documentation

| File | Changes |
|------|---------|
| [README.md](file:///d:/StockResearch/README.md) | Added database setup, pipeline usage, notebook instructions, research methodology, new API docs |

---

## Verification Results

### Pipeline Run 1 (initial data load)
| Metric | Count |
|--------|-------|
| News headlines inserted | 489 |
| Stock price rows inserted | 7,426 |
| Research metrics inserted | 337 |
| Symbols covered | 5 stocks + 1 benchmark |
| Total time | 31.9 seconds |

### Pipeline Run 2 (duplicate safety)
| Metric | Count |
|--------|-------|
| News headlines inserted | **0** (489 skipped) |
| Stock price rows inserted | **0** (7,426 skipped) |
| Research metrics updated | 337 (upsert) |
| Total time | 23.8 seconds |

### API Endpoints Tested
| Endpoint | Status | Result |
|----------|--------|--------|
| `GET /` | ✅ | `{"message": "Stock API Running"}` |
| `GET /stock/RELIANCE?timeframe=1M` | ✅ | 23 records |
| `GET /research/pipeline/status` | ✅ | 489 news, 7426 prices, 337 metrics |
| `GET /research/metrics/RELIANCE` | ✅ | 78 research metric records |
| `GET /research/correlation` | ✅ | n=310, Pearson r=0.039, Spearman ρ=0.071 |

### Correlation Results
- **310 sentiment-return pairs** available for analysis
- Pearson r = 0.039 (p=0.490) — weak positive, not significant
- Spearman ρ = 0.071 (p=0.212) — weak positive, not significant
- Mean sentiment score: −0.092 (slightly negative bias)
- Mean 7-day return: −0.008

> [!NOTE]
> These preliminary results suggest weak sentiment-return correlation with the current sample. As more daily data accumulates via the automated pipeline, statistical power will improve.
