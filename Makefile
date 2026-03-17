TOPIC      ?= a turtle exploring a magical pond
APP_SCHEME  = meta_ai_app
APP_PROJECT = meta_ai/meta_ai_app.xcodeproj
APP_BUNDLE  = meta_ai/meta_ai_app.app
VENV        = .venv/bin/python

.PHONY: video video_test build-app open-app kill-app content_test voice_test ollama-start

## Run full pipeline
video: ollama-start open-app
	PYTHONPATH=$(PWD) $(VENV) agent_ai/agent.py "$(TOPIC)"

## Run video generation test (force kill + relaunch app)
video_test: open-app
	PYTHONPATH=$(PWD) $(VENV) vision_ai/video_gen.py

## Run content generation test
content_test: ollama-start
	PYTHONPATH=$(PWD) $(VENV) content_ai/content_gen.py

## Run voice generation test
voice_test:
	PYTHONPATH=$(PWD) $(VENV) audio_ai/voice_gen.py

## Build app and copy bundle into project
build-app:
	@echo "[Make] Building macOS app..."
	xcodebuild -project $(APP_PROJECT) \
		-scheme $(APP_SCHEME) \
		-configuration Debug \
		-derivedDataPath ~/Library/Developer/Xcode/DerivedData/meta_ai_app_build \
		build | xcpretty || true
	@echo "[Make] Copying app bundle into project..."
	@rm -rf $(APP_BUNDLE)
	@cp -R ~/Library/Developer/Xcode/DerivedData/meta_ai_app_build/Build/Products/Debug/$(APP_SCHEME).app $(APP_BUNDLE)
	@echo "[Make] Build done → $(APP_BUNDLE)"

## Kill app if running
kill-app:
	@pkill -x "$(APP_SCHEME)" 2>/dev/null || true

## Launch app (builds if needed)
open-app: kill-app
	@if [ -d "$(APP_BUNDLE)" ]; then \
		echo "[Make] Launching $(APP_BUNDLE)..."; \
		open $(APP_BUNDLE); \
		sleep 3; \
	else \
		echo "[Make] App not found, building first..."; \
		$(MAKE) build-app && open $(APP_BUNDLE); \
		sleep 3; \
	fi

## Ensure Ollama is running with qwen2.5:7b
ollama-start:
	@pgrep -x ollama > /dev/null || (ollama serve &> /dev/null & sleep 2)
	@ollama pull qwen2.5:7b 2>/dev/null || true