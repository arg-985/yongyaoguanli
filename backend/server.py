"""系统入口：启动 APScheduler"""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


def main():
    import django
    django.setup()

    # 启动调度器
    from apps.plans.scheduler import start_scheduler
    start_scheduler()

    # 再启动 Django
    from django.core.management import execute_from_command_line
    import sys
    # 确保传入 manage.py 参数
    args = sys.argv[:]
    if not args or args[0].endswith('runserver') or 'runserver' not in ' '.join(args):
        if len(args) < 2:
            args.append('runserver')
    execute_from_command_line(args)


if __name__ == '__main__':
    main()
