from setuptools import setup, find_packages

setup(
    name='FoodRE1',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'Flask==2.1.2',
        'Flask-Cors==3.0.10',
        'pycryptodome==3.10.4',
        'PyJWT==2.3.0',
        'requests==2.26.0',
    ],
    entry_points={
        'console_scripts': [
            'FoodRE1=application:application',
        ],
    },
)
