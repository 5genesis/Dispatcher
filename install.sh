#! /bin/bash

# Usage:
# ./dispatcher.sh
#
# Example of entry config file:
# 
# [mano]
# PROTOCOL=http
# HOST=192.168.33.102
# PORT=5001
# PATH=/
# 
# [elcm]
# PROTOCOL=http
# HOST=192.168.33.101
# PORT=5001
# PATH=/
# 
# [validator]
# PROTOCOL=http
# HOST=validator
# PORT=5100
# PATH=/
#

config_file="dispatcher.conf"
output_file="nginx.conf"
swagger_file="swagger/template_auth.json"

echo "Platform Name: "
read answer
echo $answer > auth/platform_name
uuidgen > auth/platformID

# Check the user has configured the dispatcher config file
while true; do
    read -p "Have you prepared the '$config_file' file? " yn
    case $yn in
        [Yy]* ) echo "Let's proceed"; break;;
        [Nn]* ) echo "Please, fill in '$config_file' in the proper way"; exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

# Check the user has configured the validator env file
while true; do
    read -p "Have you prepared the Validator environment file in the 'validator' folder? " yn
    case $yn in
        [Yy]* ) echo "Let's continue"; break;;
        [Nn]* ) echo "Please, fill in Validator 'config.env' in the proper way"; exit;;
        * ) echo "Please answer yes or no.";;
    esac
done


#copy the docker-compose template to the final docker-compose file
cp docker-compose.tmp docker-compose.yml

# Add the local IP to the swagger file
my_ip=$(ip route get 8.8.8.8 | awk -F"src " 'NR==1{split($2,a," ");print a[1]}')
sed "s/DISPATCHER/$my_ip/g" $swagger_file > swagger/swagger.json

echo "Dispatcher configured using information from '$config_file' file"

sudo apt-get install python3
apt install python3-pip -y
pip3 install configparser

python3 setup.py
# Build the images
echo "Building the images..."
docker-compose -f docker-compose.yml build

echo "DONE"