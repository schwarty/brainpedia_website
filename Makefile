all:
	python pages.py
	chromium-browser /tmp/brainpedia/home.html &
