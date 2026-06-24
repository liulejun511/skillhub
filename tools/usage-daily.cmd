@echo off
rem Wrapper so the daily job runs python inside a console (avoids the no-console
rem 0xC000013A teardown under Task Scheduler) and logs output. Schedule THIS file.
if not exist "%~dp0..\.work" mkdir "%~dp0..\.work"
python "%~dp0usage-daily.py" 1>> "%~dp0..\.work\usage-daily.log" 2>&1
