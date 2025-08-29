#!/bin/bash

# install apt packages
if type apt &>/dev/null; then
  sudo apt install -y $(cat apt-packages.txt)
else
  echo "This does not appear to be an ubuntu VM."
  exit 1
fi

# install bat via deb package as it isn't available in Debian 10
if ! type bat &>/dev/null; then
  wget https://github.com/sharkdp/bat/releases/download/v0.15.4/bat_0.15.4_amd64.deb
  sudo dpkg -i ./bat_0.15.4_amd64.deb
  rm bat_0.15.4_amd64.deb
fi

# install python dependencies
if type uv &>/dev/null; then
  uv sync
else
  python3.9 -m pip install -r requirements.txt
fi
