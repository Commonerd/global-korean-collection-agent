GOAL ?= Global Korean business

install:
	python -m pip install -r requirements.txt

test:
	pytest -q

mock:
	python -m agent.main --mode once

collect-once:
	MODE=production DRY_RUN=false ENABLE_PLACES=true ./.venv/bin/python -m agent.main --mode once --goal "$(GOAL)"

loop:
	python -m agent.main --mode loop --iterations 10

long-loop:
	MODE=production DRY_RUN=false ENABLE_PLACES=true MAX_DEPTH=4 MAX_REQUESTS_PER_RUN=120 MAX_REQUESTS_PER_DOMAIN=12 MAX_NEW_ENTITIES_PER_RUN=50 MAX_RUNTIME_SECONDS=1800 ./.venv/bin/python -m agent.main --mode loop --iterations 12 --goal "$(GOAL)"

schedule-daily:
	mkdir -p "$$HOME/Library/LaunchAgents"
	sed 's|/Users/REPLACE_ME/Documents/global-korean-collection-agent|$(CURDIR)|g' launchd/com.global-korean-collection-agent.plist.example > "$$HOME/Library/LaunchAgents/com.global-korean-collection-agent.plist"
	-launchctl unload "$$HOME/Library/LaunchAgents/com.global-korean-collection-agent.plist"
	launchctl load "$$HOME/Library/LaunchAgents/com.global-korean-collection-agent.plist"

status:
	python -m agent.main --mode status

review:
	python -m agent.main --mode review
