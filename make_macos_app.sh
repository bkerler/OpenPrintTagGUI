export LC_ALL=en_US.utf8
pip3 install briefcase
rm -rf build/
rm -rf dist/
rm -rf logs/
briefcase create macOS app
briefcase build macOS app
briefcase package macOS app

