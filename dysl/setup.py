from setuptools import setup
from dysl.version import __version__

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='dysl',
      #version='2.0',
      version=__version__,
      description='Do you speak London?',
      long_description=readme(),
      url='https://github.com/meedan/dysl',
      author='Tarek Amr',
      updates='Clarissa Castellã Xavier'
      license='MIT',
      packages=['dysl', 
                'dysl.dyslib', 
                'dysl.corpora', 
                'dysl.corpora.corpuslib'],
      include_package_data=True,
      zip_safe=False)
