import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
	long_description = fh.read()

requires_list = [
    'fasteners'
]

setuptools.setup(
	name="xlab",
	version="0.0.11",
	author="Cesar Salcedo",
	author_email="cesar.salcedo@utec.edu.pe",
	description="Experiment execution tool for automation in research-oriented projects.",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/csalcedo001/xlab",
	packages=setuptools.find_packages(),
	classifiers=[
		"Programming Language :: Python :: 3",
                "License :: OSI Approved :: Apache Software License",
		"Operating System :: OS Independent",
	],
	python_requires='>=3.6',
	install_requires=requires_list,
	entry_points={
		'console_scripts':[
			'xlab=xlab.cli:main'
		]
	}
)
