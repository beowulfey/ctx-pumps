# CTX Pumps
Python software for controlling New Era Syringe Pumps
Written for chemotaxis experiments for C. elegans by Aaron Wolfe. 
Circa 2024. 

Setup instructions: 
Prereqs: python 3.12 and pipenv
Also, build a wheel for my custom NESP-lib. 


git clone this directory and enter it
pipenv shell --python 3.12
pipenv install
pip install [your nesp-lib wheel you built]

marimo edit mo-pumps.py
