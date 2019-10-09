# import os, sys
# from django.conf import settings
# import time
# import celery
# app = settings.CELERY
#
#
# class MyTask(app.Task):
#     def on_failure(self, exc, task_id, args, kwargs, einfo):
#         print('{0!r} failed: {1!r}'.format(task_id, exc))
#         print(args,  'args')
#         print(kwargs, 'kwargs')
#         print(einfo, 'einfo')
#     #
#
#     def on_success(self, retval, task_id, args, kwargs):
#         print(retval, 'retval')
#         print(task_id, 'taskid')
#         print(args, 'args')
#         print(kwargs, 'kwargs')
#
#
# @app.task(base=MyTask)
# def f1(x, y):
#     time.sleep(2)
#     print(x + y)
#     # raise ValueError
#     print("hello")
#     return "hello return!"