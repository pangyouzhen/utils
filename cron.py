from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import subprocess

scheduler = BlockingScheduler()

def run_cmd(cmd):
    print(f"Running: {cmd}")
    subprocess.call(cmd, shell=True)

# 例如模拟 crontab:  */5 * * * *
scheduler.add_job(
    lambda: run_cmd("python my_task.py"),
    CronTrigger.from_crontab("*/5 * * * *")
)

scheduler.start()
