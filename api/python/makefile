.PHONY: clean

.venv/bin/activate: requirements.txt
	rm -rf .venv
	(python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt)

clean:
	rm -rf .venv