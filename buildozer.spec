[app]
title = Крестики-Нолики
package.name = tictactoe
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,json,txt
version = 1.0
requirements = python3,pygame==2.5.2  # Обрати внимание на ДВОЙНОЕ РАВНО
orientation = portrait
fullscreen = 1
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25c
android.accept_sdk_license = True

[buildozer]
log_level = 2
