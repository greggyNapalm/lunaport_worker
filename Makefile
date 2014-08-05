test:
		nosetests tests

coverage:
		nosetests --with-coverage --cover-html --cover-html-dir=html_cover --cover-package=lunaport_worker

lint:
	@echo "Linting Python files"
	PYFLAKES_NODOCTEST=1 flake8 . --max-line-length=99
	@echo ""

deb:
	debuild; dh_clean; cd ..; dupload; cd -
