.PHONY: html

HTMLPATH?=$(pwd)

# initialize virtual environment in local folder
# same as:
# $ virtualenv -p /usr/local/bin/python3.7 venv3.37
# $ source venv3.7/bin/activate
# $ python3.7 -m pip install -r requirements.txt
init:
	( \
		virtualenv -p /usr/local/bin/python3.7 venv3.7; \
  	. ./venv3.7/bin/activate; \
		python --version; \
		python3.7 -m pip install -r requirements.txt; \
	)

# install missing packages newly added to requirements.txt
install:
	( \
    . ./venv3.7/bin/activate; \
    python --version; \
    python3.7 -m pip install -r requirements.txt; \
  )

# start jupyter notebook in virtual environment 
start:
	( \
		. venv3.7/bin/activate; \
		jupyter notebook \
	)

# Use as follows:
# $ make html HTMLPATH=./value_vs_rewards/
html:
	( \
    . ./venv3.7/bin/activate; \
		jupyter nbconvert --to html $(HTMLPATH)*.ipynb \
	) 

clean:
	-rm -i $(HTMLPATH)*.html

