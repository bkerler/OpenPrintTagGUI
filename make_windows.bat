@echo off
rd /S /Q build
rd /S /Q dist
pip3 install briefcase
briefcase create windows
briefcase build windows
briefcase package windows -i 8b5f17c056bf5eb66151e95b86831d32cd037dfe

