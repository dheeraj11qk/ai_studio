TOPIC ?= a turtle exploring a magical pond
APP_SCHEME = meta_ai_app
APP_PROJECT = meta_ai/meta_ai_app.xcodeproj
DERIVED_DATA = $(HOME)/Library/Developer/Xcode/DerivedData
VENV = .venv/bin/python

.PHONY: video build-app open-app kill-app content_test ollama-start voice_test install


## Run full pipeline: make video TOPIC="your topic here"
video: build-app open-app ollama-start ollama-start
	$(VENV) agent_ai/agent.py "$(TOPIC)"

video_test: build-app open-app
	$(VENV) vision_ai/video_gen.py


## Ensure Ollama is running with qwen2.5:7b
ollama-start:
	@echo "[Make] Checking Ollama..."
	@pgrep -x ollama > /dev/null || (ollama serve &> /dev/null & sleep 3 && echo "[Make] Ollama started.")
	@ollama pull qwen2.5:7b 2>/dev/null || true
	@echo "[Make] Ollama ready with qwen2.5:7b"
## Run content generation test
content_test: ollama-start
	PYTHONPATH=$(PWD) $(VENV) content_ai/content_gen.py

## Run voice generation test
voice_test:
	PYTHONPATH=$(PWD) $(VENV) audio_ai/voice_gen.py

## Build the macOS app via xcodebuild
build-app:
	@echo "[Make] Building macOS app..."
	xcodebuild -project $(APP_PROJECT) \
		-scheme $(APP_SCHEME) \
		-configuration Debug \
		-derivedDataPath $(DERIVED_DATA)/meta_ai_app_build \
		build | xcpretty || true
	@echo "[Make] Build done."

## Kill the app if it's running
kill-app:
	@echo "[Make] Killing $(APP_SCHEME) if running..."
	@pkill -x "$(APP_SCHEME)" 2>/dev/null && echo "[Make] App killed." || echo "[Make] App was not running."
	@sleep 1

## Open/launch the built app (kills existing instance first)
open-app: kill-app
	@echo "[Make] Launching macOS app..."
	@APP_PATH=$$(find $(DERIVED_DATA)/meta_ai_app_build -name "$(APP_SCHEME).app" -type d 2>/dev/null | head -1); \
	if [ -n "$$APP_PATH" ]; then \
		open "$$APP_PATH"; \
		echo "[Make] App launched: $$APP_PATH"; \
		sleep 5; \
	else \
		echo "[Make] App not found, trying default DerivedData..."; \
		open $$(find $(DERIVED_DATA) -name "$(APP_SCHEME).app" -type d 2>/dev/null | head -1); \
		sleep 5; \
	fi
