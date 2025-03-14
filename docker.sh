#!/bin/bash

get_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    else
        echo "unknown"
    fi
}

install_docker() {
    distro=$1
    echo "[INFO] Distro: $distro"

    if grep -qiE 'debian|ubuntu|kali|parrot|linuxmint|elementary|pop' /etc/*release; then
        sudo apt-get update && sudo apt-get install -y docker.io
    elif grep -qiE 'rhel|centos|rocky|almalinux' /etc/*release; then
        sudo yum install -y docker
    elif grep -qiE 'fedora' /etc/*release; then
        sudo dnf install -y docker
    elif grep -qiE 'arch|manjaro|arcolinux|endeavouros|garuda|artix' /etc/*release; then
        sudo pacman -Sy docker --noconfirm
    else
        echo "[ERROR] Unsupported distro: $distro"
        exit 1
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "[INFO] Docker is not installed. Starting installation..."
        install_docker "$(get_distro)"
    else
        echo "[INFO] Docker is already installed."
    fi
}
check_docker_service() {
    if ! systemctl is-active --quiet docker; then
        echo "[INFO] Docker service is not running. Starting and enabling..."
        sudo systemctl start docker
        sudo systemctl enable docker
    else
        echo "[INFO] Docker service is already active."
    fi
}

check_mongodb_container() {
    if sudo docker inspect mongodb1 &>/dev/null; then
        running_status=$(sudo docker inspect -f '{{.State.Running}}' mongodb1 2>/dev/null)
        running_status=$(echo "$running_status" | tr '[:upper:]' '[:lower:]' | xargs)
        
        if [ "$running_status" != "true" ]; then
            echo "[INFO] MongoDB container exists but is not running. Starting..."
            sudo docker start mongodb1
        else
            echo "[INFO] The MongoDB container is already running."
        fi
    else
        echo "[INFO] MongoDB container does not exist. Creating..."
        sudo docker run -d -p 27017:27017 --name mongodb1 mongo:4
    fi
}

verify_mongodb() {
    running_status=$(sudo docker inspect -f '{{.State.Running}}' mongodb1 2>/dev/null)
    running_status=$(echo "$running_status" | tr '[:upper:]' '[:lower:]' | xargs)

    if [ "$running_status" == "true" ]; then
        echo "[SUCCESS] The MongoDB container is running successfully."
    else
        echo "[ERROR] MongoDB container is not running."
        exit 1
    fi
}

check_docker
check_docker_service
check_mongodb_container
verify_mongodb
