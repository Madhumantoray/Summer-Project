# Scheduler Examples

Schedule `run_daily_pipeline.py` to run automatically after NSE market close (after 16:00 IST).

## Windows Task Scheduler

1. Open **Task Scheduler** → Create Basic Task
2. Set trigger: **Daily** at **16:30**
3. Set action: **Start a program**
   - Program: `D:\StockResearch\backend\venv\Scripts\python.exe`
   - Arguments: `scripts/run_daily_pipeline.py`
   - Start in: `D:\StockResearch\backend`

Or import this XML:

```xml
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-01-01T16:30:00+05:30</StartBoundary>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>D:\StockResearch\backend\venv\Scripts\python.exe</Command>
      <Arguments>scripts/run_daily_pipeline.py</Arguments>
      <WorkingDirectory>D:\StockResearch\backend</WorkingDirectory>
    </Exec>
  </Actions>
  <Settings>
    <Enabled>true</Enabled>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
  </Settings>
</Task>
```

## Linux Cron

```bash
# Run daily at 16:30 IST (11:00 UTC)
0 11 * * 1-5 cd /path/to/StockResearch/backend && ./venv/bin/python scripts/run_daily_pipeline.py >> /var/log/stock_pipeline.log 2>&1
```

Notes:
- `1-5` = Monday to Friday only (skip weekends)
- Adjust UTC offset for your timezone

## Python `schedule` Library

```python
import schedule
import subprocess
import time

def run():
    subprocess.run([
        r"D:\StockResearch\backend\venv\Scripts\python.exe",
        "scripts/run_daily_pipeline.py",
    ], cwd=r"D:\StockResearch\backend")

# Run at 16:30 every day
schedule.every().day.at("16:30").do(run)

while True:
    schedule.run_pending()
    time.sleep(60)
```
