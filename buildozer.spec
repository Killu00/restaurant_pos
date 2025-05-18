[app]
title = Restaurant POS
package.name = restaurantpos
package.domain = org.tristan
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,db,txt,json,csv
version = 1.0

icon.filename = data/icon.png
presplash.filename = data/splash.png

orientation = landscape
fullscreen = 1

# Permissions (CSV writing, file management)
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.allow_backup = 1
android.manage_external_storage = True

# Architectures to build for
android.archs = arm64-v8a,armeabi-v7a

# API and NDK settings
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21

# ✅ Explicit Python version (important!)
python_version = 3.10

# Dependencies
requirements = kivy==2.3.1,bcrypt,cython==0.29.28,pyjnius==1.4.1, jinja2,setuptools,toml


# Enable sqlite3 support
android.sqlite3 = true

# SDL2 (used by Kivy)
bootstrap = sdl2

# APK build target
android.packaging = apk

# Fix for WSL
copy_libs = 1
