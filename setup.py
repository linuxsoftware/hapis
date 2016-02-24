[nosetests]
match=^test
nocapture=1
cover-package=hapis
with-coverage=1
cover-erase=1

[compile_catalog]
directory = hapis/locale
domain = hapis
statistics = true

[extract_messages]
add_comments = TRANSLATORS:
output_file = hapis/locale/hapis.pot
width = 80

[init_catalog]
domain = hapis
input_file = hapis/locale/hapis.pot
output_dir = hapis/locale

[update_catalog]
domain = hapis
input_file = hapis/locale/hapis.pot
output_dir = hapis/locale
previous = true
