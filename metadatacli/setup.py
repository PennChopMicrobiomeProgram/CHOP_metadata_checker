import setuptools

setuptools.setup(
    name='metadatacli',
    version="0.0.1",
    description='CLI to create custom metadata upload links for CHOP metadata checker website',
    author='Charlie Bushman',
    author_email='ctbushman@gmail.com',
    url='https://github.com/PennChopMicrobiomeProgram/CHOP_metadata_checker',
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    entry_points={
        'console_scripts': [
            'metadatacli=metadatacli.command:main',
        ],
    },
    install_requires=[
        
    ],
    classifiers=[
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ],
    license='GPLv2+',
)