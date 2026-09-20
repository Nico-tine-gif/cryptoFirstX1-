[app]
title = CryptoFirstX1
package.name = cryptofirstx1
package.domain = org.nicotinegif
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json
source.include_patterns = core/*,tests/*,scripts/*
version = 0.1

# FIX 1: Changed python3.11 to python3
requirements = python3,kivy,requests

orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 31
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True

# FIX 2: Added this to stop the compiler from crashing on warnings
android.ndk_allows_werror = False
