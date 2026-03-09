@echo off
echo Looking for %2 in %1...
echo.
findstr /n "%2" %1
echo.
echo To view the function, use: type %1 ^| more