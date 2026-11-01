"""
APScheduler 定时任务配置
- 用药提醒生成：每天为活跃用药计划生成未来7天的 PlanReminder
- 漏服自动判定：每15分钟扫描超时未服的提醒，置为 MISSED
"""
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


def generate_reminders_for_active_plans():
    """为所有活跃的用药计划生成未来7天的待服提醒"""
    try:
        import django
        django.setup()

        from apps.plans.models import MedicationPlan, PlanReminder

        now = datetime.now()
        end_window = now + timedelta(days=7)
        created_count = 0

        active_plans = MedicationPlan.objects.filter(
            is_active=True,
            start_date__lte=now.date(),
        ).exclude(end_date__isnull=False, end_date__lt=now.date())

        for plan in active_plans:
            times = _expand_times(plan)
            # 为每天的每个时间点生成提醒
            current = now.replace(hour=0, minute=0, second=0, microsecond=0)
            while current <= end_window:
                for t in times:
                    dt = datetime.combine(current.date(), t)
                    # 只生成未来的
                    if dt < now:
                        continue
                    exists = PlanReminder.objects.filter(plan=plan, scheduled_time=dt).exists()
                    if not exists:
                        PlanReminder.objects.create(plan=plan, scheduled_time=dt)
                        created_count += 1
                current += timedelta(days=1)

        logger.info(f"[APScheduler] 生成用药提醒 {created_count} 条")
    except Exception as e:
        logger.exception(f"[APScheduler] 生成提醒异常: {e}")


def ensure_reminders_for_date(day):
    """确保指定日期存在提醒（调度器未运行时的兜底）。

    与 generate_reminders_for_active_plans 不同，这里不跳过当天已过的时间点，
    这样用户仍能补记当天早先的服药。
    """
    try:
        from datetime import datetime

        from apps.plans.models import MedicationPlan, PlanReminder

        plans = MedicationPlan.objects.filter(
            is_active=True, start_date__lte=day
        ).exclude(end_date__isnull=False, end_date__lt=day)

        created = 0
        for plan in plans:
            for t in _expand_times(plan):
                dt = datetime.combine(day, t)
                if not PlanReminder.objects.filter(plan=plan, scheduled_time=dt).exists():
                    PlanReminder.objects.create(plan=plan, scheduled_time=dt)
                    created += 1
        return created
    except Exception:
        logger.exception('[提醒兜底] 生成当日提醒失败')
        return 0


def mark_missed_reminders():
    """扫描超时 30 分钟未处理的提醒，自动置为漏服"""
    try:
        import django
        django.setup()

        from apps.plans.models import PlanReminder
        from apps.records.models import MedicationRecord

        threshold = datetime.now() - timedelta(minutes=30)
        pending = PlanReminder.objects.filter(
            status='PENDING',
            scheduled_time__lt=threshold,
        )

        missed_count = 0
        for reminder in pending:
            reminder.status = 'MISSED'
            reminder.save()

            # 同步写入 MedicationRecord（便于后续统计）
            MedicationRecord.objects.get_or_create(
                reminder=reminder,
                defaults={
                    'plan': reminder.plan,
                    'patient': reminder.plan.patient,
                    'medication': reminder.plan.medication,
                    'scheduled_time': reminder.scheduled_time,
                    'taken_time': reminder.scheduled_time,
                    'status': 'MISSED',
                    'delay_minutes': 0,
                }
            )
            missed_count += 1

        if missed_count:
            logger.info(f"[APScheduler] 判定漏服 {missed_count} 条")
    except Exception as e:
        logger.exception(f"[APScheduler] 漏服判定异常: {e}")


def _expand_times(plan):
    """根据计划频率展开为一天中的时间点（HH:MM）"""
    from datetime import time

    freq = plan.frequency

    if plan.custom_times and isinstance(plan.custom_times, list) and len(plan.custom_times) > 0:
        times = []
        for t in plan.custom_times:
            if isinstance(t, str):
                try:
                    hh, mm = t.split(':')
                    times.append(time(int(hh), int(mm)))
                except Exception:
                    pass
        if times:
            return times

    mapping = {
        'DAILY': [time(8, 0)],
        'ONCE_DAILY': [time(8, 0)],
        'BID': [time(8, 0), time(20, 0)],
        'TID': [time(8, 0), time(12, 0), time(20, 0)],
        'QID': [time(6, 0), time(12, 0), time(18, 0), time(23, 0)],
    }
    return mapping.get(freq, [time(8, 0)])


def start_scheduler():
    """启动 APScheduler（仅在主进程中调用）"""
    import os
    # Django runserver 自动重载会启动两个进程，只在主进程中启动调度器
    if os.environ.get('RUN_MAIN') != 'true':
        return

    try:
        scheduler = BackgroundScheduler(timezone='Asia/Shanghai')

        # 每天凌晨 00:10 生成未来 7 天的提醒
        scheduler.add_job(
            generate_reminders_for_active_plans,
            trigger=CronTrigger(hour=0, minute=10),
            id='generate_reminders',
            replace_existing=True,
        )

        # 每 15 分钟执行一次漏服判定
        scheduler.add_job(
            mark_missed_reminders,
            trigger=IntervalTrigger(minutes=15),
            id='mark_missed',
            replace_existing=True,
        )

        scheduler.start()
        logger.info("[APScheduler] 调度器已启动")
    except Exception as e:
        logger.exception(f"[APScheduler] 启动失败: {e}")
