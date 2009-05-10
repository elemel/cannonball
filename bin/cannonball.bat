@echo off
set CANNONBALL_ROOT=%0\..\..
set PYTHONPATH=%PYTHONPATH%:%CANNONBALL_ROOT%\lib
python -m cannonball.main %*