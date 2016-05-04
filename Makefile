init:
	pip install -r requirements.txt

clean:
	find . -name "*.pyc" -exec rm -rf {} \;
