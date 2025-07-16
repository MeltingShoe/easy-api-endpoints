#!/usr/bin/env bash
:; kill -9 $(ps aux | grep "run-server.py" | awk '{print $2}') ; exit 0
cls
taskkill /IM webhook.exe /F