import taskiq_fastapi

from purch.core.taskiq import setup_taskiq_broker_and_scheduler

broker, scheduler = setup_taskiq_broker_and_scheduler()

taskiq_fastapi.init(broker, "purch.main:app")
