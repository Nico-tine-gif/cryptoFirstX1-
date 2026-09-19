[app]
title = CryptoFirstX1
package.name = cryptofirstx1
package.domain = org.nicotinegif
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json
source.include_patterns = core/*,tests/*,scripts/*
version = 0.1
requirements = python3.11,kivy,requests
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 31
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True
