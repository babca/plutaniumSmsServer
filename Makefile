init:
	pip install -r requirements.txt

clean:
	find . -name "*.pyc" -exec rm -rf {} \;

fixperms:
	find . -type d -print0 | xargs -0 chmod 0775
	find . -type f -print0 | xargs -0 chmod 0664

