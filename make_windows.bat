@echo off
rd /S /Q build
rd /S /Q dist
pip3 install briefcase
briefcase create windows
briefcase build windows
briefcase package windows

