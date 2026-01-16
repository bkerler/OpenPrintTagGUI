export LC_ALL=en_US.utf8
sudo apt install docker.io docker-buildx -y
pip3 install briefcase
rm -rf build/
rm -rf dist/
rm -rf logs/
briefcase create linux flatpak
briefcase build linux flatpak
briefcase package linux flatpak

