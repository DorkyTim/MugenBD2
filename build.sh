#!/bin/bash

# Build the PyInstaller executable
pyinstaller codes/main.py \
  --onefile \
  --clean \
  --noconsole \
  --name MugenGSv3 \
  --exclude-module tkinter \
  --exclude-module test \
  --exclude-module PyQt5.QtWebEngineWidgets \
  --exclude-module PyQt5.QtMultimediaWidgets \
  --exclude-module PyQt5.QtPrintSupport \
  --add-data "BD2_best.pt;." \
  --add-data ".env;."