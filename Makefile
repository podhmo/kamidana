readme:
	rm -f README.rst
	cat misc/_README.header.rst > README.rst
	PYTHONPATH=misc/bin/ python misc/bin/readme.py >> README.rst
	PYTHONPATH=misc/bin/ python misc/bin/readme2.py >> README.rst
