install:
	python -m pip install -r requirements.txt

test:
	pytest -q

mock:
	python -m agent.main --mode once

loop:
	python -m agent.main --mode loop --iterations 10

status:
	python -m agent.main --mode status

review:
	python -m agent.main --mode review
