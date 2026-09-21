[app]
title = cryptoFirstX1
package.name = cryptofirstx1
package.domain = org.cryptofirstx1

source.dir = .
source.include_exts = py,txt,json,ttf,png,jpg,kv,atlas
source.exclude_dirs = tests,.git,.buildozer,__pycache__,bin,logs
source.exclude_patterns = *.pyc,*.pyo,*.apk,*.aab,requirements.txt

version = 0.1.0

# buildozer splits on commas -> no "<" upper bounds here.
# If you want the ranges from requirements.txt, keep them there and
# install at runtime; p4a recipes pin their own versions anyway.
requirements = python3,requests,cryptography,openssl,sqlite3

android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True

# Headless supervisor — no Kivy window required.
p4a.bootstrap = service_only

[buildozer]
log_level = 2
warn_on_root = 1
