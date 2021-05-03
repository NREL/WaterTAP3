from setuptools import setup, find_namespace_packages

setup(
        name='watertap3',
        version='0.0.1',
        # packages=['watertap3/build', 'watertap3/wt_units'],
        packages=find_namespace_packages(),
        url='https://github.com/NREL/NAWI-WaterTAP3',
        license='',
        author='WaterTAP3 Team',
        author_email='ariel.miara@nrel.gov',
        description='WaterTAP3 Technoeconomic Tool'
        )