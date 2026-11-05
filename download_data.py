"""Download the original UCI archive; excluded from version control."""
from pathlib import Path
from urllib.request import urlretrieve
p=Path('data/uci322.zip');p.parent.mkdir(exist_ok=True)
urlretrieve('https://archive.ics.uci.edu/static/public/322/gas+sensor+array+under+dynamic+gas+mixtures.zip',p)
print(p)
