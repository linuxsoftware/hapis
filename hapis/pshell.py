# myapp/lib/pshell.py
from webtest import TestApp
from h1 import models
import inspect

def setup(env):
    env.update((name, cls) for name, cls in
               inspect.getmembers(models, inspect.isclass))
    env['DBSession'] = models.DBSession
    env['request'].host = 'www.example.com'
    env['request'].scheme = 'https'
    env['testapp'] = TestApp(env['app'])
