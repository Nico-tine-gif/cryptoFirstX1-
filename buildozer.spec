[app]
# (str) Title of your application
title = CryptoFirstX1

# (str) Package name
package.name = cryptofirstx1

# (str) Package domain (needed for android/ios packaging)
package.domain = org.nicotinegif

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,txt,json

# Include your specific folders
source.include_patterns = core/*,tests/*,scripts/*

# (str) Application versioning
version = 0.1

# (str) App orientation
orientation = portrait

# (str) App fullscreen
fullscreen = 0

# --- CRITICAL FIX FOR YOUR PYTHON ERRORS ---
# Pinning both hostpython3 and python3 to the SAME version fixes the mismatch.
# We also pin Cython to 0.29.33 because newer versions break Kivy's pyjnius.
requirements = python3==3.11.1, hostpython3==3.11.1, kivy==2.3.0, cython==0.29.33, requests

# --- PERMISSIONS ---
android.permissions = INTERNET

# --- ANDROID BUILD SETTINGS ---
android.api = 31
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True

# --- CRITICAL FIX FOR THE -Werror CRASHES IN YOUR LOGS ---
# This tells the NDK to ignore unknown compiler warnings instead of crashing.
android.ndk_allows_werror = False
