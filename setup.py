import os
import re
from setuptools import setup, find_packages


base_path = os.path.dirname(__file__)

# Get the version (borrowed from SQLAlchemy)
fp = open(os.path.join(base_path, 'lunaport_worker', '__init__.py'))
VERSION = re.compile(r".*__version__ = '(.*?)'",
                     re.S).match(fp.read()).group(1)
fp.close()

setup(
    name = 'lunaport_worker',
    version = VERSION,
    author = 'Gregory Komissarov',
    author_email = 'gregory.komissarov@gmail.com',
    description = 'Lunaport service offline tasks performer.',
    long_description='\n' + open('README.rst').read() + '\n\n' + open('CHANGES.rst').read(),
    license = 'BSD',
    url = 'https://github.domain/napalm/lunaport_worker',
    keywords = ['load', 'celery'],
    packages = [
        'lunaport_worker',
        'lunaport_worker.tasks',
        'lunaport_worker.notify',
    ],
    zip_safe = False,
    install_requires=[
        #'requests==1.2.3',
        #'celery==3.0.15',
    ],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Distributed Computing',
    ],
)
