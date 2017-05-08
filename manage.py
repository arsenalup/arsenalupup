#!/usr/bin/env python
import os
COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

from app import create_app, db
from app.models import User, Follow, Role, Permission, Post, Comment
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Follow=Follow, Role=Role,
                Permission=Permission, Post=Post, Comment=Comment)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

@manager.command
def initdata():
    """ cretat a new data"""
    db.create_all()
    admin_role =Role(name = 'Administrator')
    mod_role = Role(name = 'Moderator')
    user_role =Role(name = 'User')
    user_john=User(username='Arsenal',role=admin_role,confirmed=True,email='676250063@qq.com',
                        password='cky1993717')
    user_susan = User(username='susan', role=user_role, confirmed=True, email='xxxxx@qq.com',
                      password='xxxxxxx')
    user_david = User(username='david', role=user_role, confirmed=True, email='xxxxxx@qq.com',
                      password='xxxxxxxx')
    db.session.add_all([admin_role, mod_role, user_role, user_john, user_susan, user_david])
    db.session.commit()
    Role.insert_roles()
    User.generate_fake(3)
    Post.generate_fake(3)

@manager.command
def drop():
    """
    drop the database
    """
    db.drop_all()

@manager.command
def test(coverage=False):
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()



@manager.command
def profile(length=25, profile_dir=None):
    """Start the application under the code profiler."""
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()



@manager.command
def deploy():
    """Run deployment tasks."""
    from flask_migrate import upgrade
    from app.models import Role, User

    # migrate database to latest revision
    upgrade()

    # create user roles
    Role.insert_roles()

    # create self-follows for all users
    User.add_self_follows()


if __name__ == '__main__':
    manager.run()
