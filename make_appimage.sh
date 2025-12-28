sudo apt install docker.io docker-buildx -y
pip3 install briefcase
rm -rf build/
rm -rf dist/
briefcase create linux appimage
briefcase build linux appimage
briefcase package linux appimage

