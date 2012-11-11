try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='mongo-blog',
    version='0.1',
    description='Blog with mongodb backend',
    author='Hugh Brown',
    author_email='hughdbrown@yahoo.com',
    url='http://iwebthereforeiam.com/',
    install_requires=[
        'nose==1.2.1',
    ],
    tests_require=[
        'nose==1.2.1',
        'coverage==3.5.3',
        'pylint==0.26.0',
        'pep8==1.3.3',
        'pyflakes==0.5.0',
    ],
    setup_requires=[],
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    test_suite='nose.collector',
    zip_safe=False,
)
