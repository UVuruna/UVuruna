@echo off
rem Shim so `uv <cmd>` works from any project folder once rules\tools is on
rem PATH. Everything else lives in uv.py (see rules\howto\runner.md).
python "%~dp0uv.py" %*
