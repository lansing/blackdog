#!/bin/bash

set -e

repo_zip=https://github.com/lansing/blackdog/archive/refs/heads/master.zip

tmp_download_file=/tmp/blackdog.zip
install_dir=/opt/blackdog
venv_dir=$install_dir/venv


if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root."
    exit 1  # Exit with error code 1
fi

dev=false

# TODO this doesn't seem to work
# We want to get the flag -d
while getopts ":d" opt; do
  case $opt in
    f)
      dev=true
      ;;
    \?)
      echo "Usage: $0 [-d]"
      exit 1
      ;;
  esac
done

delete_service() {
    local service_name=$1
    local service_path="/etc/systemd/system/${service_name}"

    # Check if the service exists
    if systemctl list-units --type=service --all | grep -q "${service_name}"; then
        # Stop the service if it is running
        sudo systemctl stop "${service_name}"
        echo "Service ${service_name} stopped."

        # Disable the service to prevent it from starting on boot
        sudo systemctl disable "${service_name}"
        echo "Service ${service_name} disabled."

        # Remove the service file
        sudo rm "${service_path}"
        echo "Service file ${service_path} removed."

        # Reload systemd to reflect the changes
        sudo systemctl daemon-reload
        echo "Systemd daemon reloaded."
    else
        echo "Service ${service_name} is not installed."
    fi
}

echo "Cleaning up any prev instal"

if [ -f $tmp_download_file ]; then
  rm $tmp_download_file
fi

if [ -d $install_dir ]; then
  rm -rf $install_dir
fi

echo "Deleting services if they are already installed"
delete_service "blackdog-display.service"
delete_service "blackdog-mpd.service"
delete_service "blackdog-shairport.service"


# Branch based on the flag
if [ "$dev" = true ]; then
  echo "Copying files from current dir"
  parent_dir=$(dirname "$(realpath "$0")")
  cp -r $parent_dir $install_dir
else
  echo "Downloading the scripts"
  wget -q $repo_zip -O $tmp_download_file && unzip -q $tmp_download_file "blackdog-master/*" -d $install_dir && rm -f $tmp_download_file && mv $install_dir/blackdog-master/* $install_dir && rm -rf $install_dir/blackdog-master
fi

echo "Creating venv"
python -m venv $venv_dir

echo "Installing Python dependencies"
$venv_dir/bin/pip install -r $install_dir/requirements.txt


## BEGIN blackdog-shairport install
echo "Installing blackdog-shairport"

echo "Installing Mosquitto"
sudo apt install -y mosquitto

echo "Modifying shairport.conf (we will back up the original!)"
sudo python $install_dir/setup/shairport_mqtt_config.py /etc/shairport-sync.conf $install_dir/setup/conf/shairport-mqtt.conf

echo "Adding blackdog-shairport systemd"
sudo cp $install_dir/systemd/blackdog-shairport.service /etc/systemd/system/blackdog-shairport.service
sudo systemctl enable blackdog-shairport.service
sudo systemctl start blackdog-shairport.service


## BEGIN blackdog-display-server install
echo "Installing blackdog-display-server"

echo "Enabling i2c and SPI"
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

echo "Adding dtoverlay=spi0-0cs to firmware config"
sudo python $install_dir/setup/fix_firmware_config.py

echo "Adding blackdog-display systemd"
sudo cp $install_dir/systemd/blackdog-display.service /etc/systemd/system/blackdog-display.service
sudo systemctl enable blackdog-display.service
sudo systemctl start blackdog-display.service

## BEGIN blackdog-mpd install
echo "Adding blackdog-mpd systemd"
sudo cp $install_dir/systemd/blackdog-mpd.service /etc/systemd/system/blackdog-mpd.service
sudo systemctl enable blackdog-mpd.service
sudo systemctl start blackdog-mpd.service

## BEGIN blackdog-screensaver
echo "Adding blackdog-screensaver systemd"
sudo cp $install_dir/systemd/blackdog-screensaver.service /etc/systemd/system/blackdog-screensaver.service
sudo systemctl enable blackdog-screensaver.service
sudo systemctl start blackdog-screensaver.service


## BEGIN cleanup and conclusion
echo "Cleaning up"
rm -rf $install_dir/systemd
rm -rf $install_dir/setup
rm -rf $install_dir/setup.sh

echo "All done. We changed some firmware setting to support the Inky display, so you might need to restart the system."


