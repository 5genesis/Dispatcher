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
#[auth]
# PROTOCOL=http
# HOST=auth
# PORT=2000
# PATH=/

config_file="dispatcher.conf"
output_file="nginx.conf"


function write_header {
echo "
events {
    worker_connections  1024;  ## Default: 1024
}

http {
    log_format   main '\$remote_addr - \$remote_user [\$time_local]  \$status '
        '\"\$request\" \$body_bytes_sent \"\$http_referer\" '
        '\"\$http_user_agent\" \"\$http_x_forwarded_for\"';
    access_log   /var/log/nginx/access.log  main;
    error_log   /var/log/nginx/error.log  debug;
    server_names_hash_bucket_size 128; # this seems to be required for some vhosts

    server {
        listen 8082 default_server;
        listen [::]:8082 default_server;
        access_log   /var/log/nginx/dispatcher.log  main;
        client_max_body_size 8000M;
        server_name localhost;" > $1
}

function write_footer {
echo "
    }
}" >> $1
}

function add_enabler {
  if [ $1 == "auth" ]; then
	         echo "

        location /$1 {
            proxy_pass $2;
            #rewrite ^/(.*)/$ /\$1 permanent;
            proxy_redirect     off;
            proxy_set_header   Host \$host;
            proxy_set_header   X-Real-IP \$remote_addr;
            proxy_set_header   X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Host \$server_name;
        }
        location = /mandatory_auth {
            internal;
            proxy_pass              http://$1:2000/validate_request;
            proxy_pass_request_body off;
            proxy_set_header        Content-Length \"\";
            proxy_set_header        X-Original-URI \$request_uri;
        }" >> $3
	else
           echo "

        location /$1 {
            auth_request     /mandatory_auth;
            auth_request_set \$auth_status \$upstream_status;
            proxy_pass $2;
            #rewrite ^/(.*)/$ /\$1 permanent;
            proxy_redirect     off;
            proxy_set_header   Host \$host;
            proxy_set_header   X-Real-IP \$remote_addr;
            proxy_set_header   X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Host \$server_name;
        }" >> $3
  fi



}


# Check the user has configured the validator env file
while true; do
    read -p "Have you prepared the Validator environment file in the 'validator' folder? " yn
    case $yn in
        [Yy]* ) echo "Let's continue"; break;;
        [Nn]* ) echo "Please, fill in Validator 'config.env' in the proper way"; exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

# Check the user has configured the dispatcher config file
while true; do
    read -p "Have you prepared the '$config_file' file? " yn
    case $yn in
        [Yy]* ) echo "Let's proceed"; break;;
        [Nn]* ) echo "Please, fill in '$config_file' in the proper way"; exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

# Before the config file is processed, the nginx config file is created and filled up
#  with the static part of the configuration
write_header $output_file

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
        add_enabler $module $line $output_file

    fi
    # Preparation of the key line that includes all the information included in the config file
    write_enabler=true
    module=$( echo $name | cut -d "[" -f2 | cut -d "]" -f1 )
    line="PROTOCOL://HOST:PORTPATH"
else
    # if the $value is not empty, we replace the variable in the key line
    line="${line//$name/$value}"
fi
done < $config_file

add_enabler $module $line $output_file


echo "Dispatcher configured using information from '$config_file' file"

# after the whole config file is processed, we write the last part of the config file
write_footer $output_file

# Build the images
echo "Building the images..."
docker-compose -f docker-compose.yml build

echo "DONE"
