from setuptools import setup, find_packages

setup(
    name='utm_projection',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'pyproj',
        'rasterio',
        'geopandas',
        
    ],
    entry_points={
        'console_scripts': [
            # If your package includes command-line scripts
            # 'my_command=my_package.module:function'
        ],
    },
    author='Rabina Twayana',
    author_email='rabinatwayana123@gmail.com',
    description='A description of your package',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/rabinatwayana/utm_projection',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)