#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
export LC_ALL=C.UTF-8

if ! command -v flatpak >/dev/null || ! command -v flatpak-builder >/dev/null ||
    ! python3 -c 'import ensurepip, venv' >/dev/null 2>&1; then
    if command -v dnf >/dev/null; then
        sudo dnf install -y flatpak flatpak-builder python3-pip
    elif command -v apt-get >/dev/null; then
        sudo apt-get update
        sudo apt-get install -y flatpak flatpak-builder python3-venv
    else
        echo "Install flatpak, flatpak-builder and Python's venv support before running this script." >&2
        exit 1
    fi
fi

python3 -m venv build/flatpak-venv
build/flatpak-venv/bin/python -m pip install briefcase
rm -rf build/openprinttaggui/linux/flatpak/
build/flatpak-venv/bin/python -m briefcase create linux flatpak --no-input
build/flatpak-venv/bin/python -m briefcase build linux flatpak --no-input
build/flatpak-venv/bin/python -m briefcase package linux flatpak --no-input
