# See: http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html
# for why we do this:
try:
    import multiprocessing
except ImportError:
    pass

from setuptools import setup


try:
    import paver.tasks
except ImportError:
    from os.path import exists
    if exists("paver-minilib.zip"):
        import sys
        sys.path.insert(0, "paver-minilib.zip")
    import paver.tasks

paver.tasks.main()



#setup(
#    name="pylithiumsso",
#    version="0.2.2",
#    description="Python Client for Lithium SSO Integration",
#    author="Alex Milstead",
#    author_email="amilstead@jawbone.com",
#    package_dir={"": "src"},
#    packages = ["pylithium"],
#    py_modules=["pylithium.client"],
#    license="MIT",
#    url="https://github.com/jawbone/pylithiumsso",
#    test_suite='nose.collector',
#    tests_require=["nose==1.2.1"],
#    install_requires=["pycrypto==2.6"]
#)
