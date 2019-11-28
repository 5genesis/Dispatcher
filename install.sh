#! /bin/bash

# Usage:
# ./dispatcher.sh <input_config_file>
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



function write_header {
echo "
events {}
http {
    server {
        listen 8082 default_server;
        listen [::]:8082 default_server;
        server_name localhost;" > $1
}

function write_footer {
echo "
    }
}" >> $1
}

function add_enabler {
echo "
        
        location /$1 {
            proxy_pass $2;
            #rewrite ^/(.*)/$ /\$1 permanent;
            proxy_redirect     off;
            proxy_set_header   Host \$host;
            proxy_set_header   X-Real-IP \$remote_addr;
            proxy_set_header   X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Host \$server_name;
        }" >> $3

}


while true; do
    read -p "Have you prepared the '$1' file? " yn
    case $yn in
        [Yy]* ) echo "Let's proceed"; break;;
        [Nn]* ) echo "Please, fill in $1 in the proper way"; exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

# Before the config file is processed, the nginx config file is created and filled up
#  with the static part of the configuration
write_header "nginx.conf"

write_enabler=false

# start the processing of the configuration file
IFS="="
while read -r name value
do
# if the line is blank, continue to the next one
if [ -z "${name}" ]
then
    continue;
fi
# Remove blanks from the strings
name=${name//[[:blank:]]/}
value=${value//[[:blank:]]/}

# if the variable "value" is empty (it means we are in the line that defines the module name
if [ -z "${value}" ]
then
    # the first time we arrive here, we don't do anything
    if $write_enabler; then
	# write the paragraph that includes all the config of the module
        add_enabler $module $line "nginx.conf"
    fi
    # Preparation of the key line that includes all the information included in the config file
    write_enabler=true
    module=$( echo $name | cut -d "[" -f2 | cut -d "]" -f1 )
    line="PROTOCOL://HOST:PORTPATH"
else
    # if the $value is not empty, we replace the variable in the key line
    line="${line//$name/$value}"
fi
done < $1

add_enabler $module $line "nginx.conf"
echo "Dispatcher configured using information from '$1' file"

# after the whole config file is processed, we write the last part of the config file
write_footer "nginx.conf"

# Build the images
docker-compose -f docker-compose.yaml build
