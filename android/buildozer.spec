[app]

title = Gabby's Tetris
package.name = gabbystetris
package.domain = io.github.gabbyzamora80
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,txt
source.exclude_dirs = .git,.buildozer,bin,__pycache__
version = 1.0.0
version.regex = __version__ = "([0-9.]+)"
version.filename = %(source.dir)s/main.py
icon.filename = icon.png
orientation = portrait
fullscreen = 0
osx.python_version = 3

requirements = python3,kivy

presplash.filename = icon.png
android.api = 36
android.minapi = 23
android.ndk = 28c
android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = True
android.debug_artifact = apk
android.release_artifact = aab
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1
