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
        listen 8082 ssl default_server;
        listen [::]:8082 ssl default_server;
        root /repository;
        ssl_certificate /etc/ssl/server.crt;
	      ssl_certificate_key /etc/ssl/server.key;

        access_log   /var/log/nginx/dispatcher.log  main;
        client_max_body_size 8000M;
        server_name localhost;

        location /repository {
            alias /repository/;
            autoindex on;
                          }" > $1
}

function write_footer_auth {
echo "

        location /auth {
            proxy_pass http://auth:2000/;
            #rewrite ^/(.*)/$ /\$1 permanent;
            proxy_redirect     off;
            proxy_set_header   Host \$host;
            proxy_set_header   X-Real-IP \$remote_addr;
            proxy_set_header   X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Host \$server_name;
            if (\$request_method = 'OPTIONS') {
                add_header 'Access-Control-Allow-Origin' '*';
                add_header 'Access-Control-Allow-Methods' 'GET, POST, DELETE, OPTIONS';
                #
                # Custom headers and headers various browsers *should* be OK with but aren't 
                #
                #add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range';
                add_header 'Access-Control-Allow-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Content-Range,Range';
                #
                # Tell client that this pre-flight info is valid for 20 days
                #
                add_header Access-Control-Allow-Headers "Authorization";
                add_header Access-Control-Allow-Credentials "true";
                add_header 'Access-Control-Max-Age' 1728000;
                add_header 'Content-Type' 'text/plain; charset=utf-8';
                add_header 'Content-Length' 0;
                return 204;
            }        
        }
        location = /mandatory_auth {
            internal;
            proxy_pass              http://auth:2000/validate_request;
            proxy_pass_request_body off;
            proxy_set_header        Content-Length \"\";
            proxy_set_header        X-Original-URI \$request_uri;
        }
    }
}" >> $1
}

function write_footer {
echo "
    }
}" >> $1
}

function add_enabler_auth {
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
            if (\$request_method = 'OPTIONS') {
                add_header 'Access-Control-Allow-Origin' '*';
                add_header 'Access-Control-Allow-Methods' 'GET, POST, DELETE, OPTIONS';
                #
                # Custom headers and headers various browsers *should* be OK with but aren't 
                #
                #add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range';
                add_header 'Access-Control-Allow-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Content-Range,Range';
                #
                # Tell client that this pre-flight info is valid for 20 days
                #
                add_header Access-Control-Allow-Headers "Authorization";
                add_header Access-Control-Allow-Credentials "true";
                add_header 'Access-Control-Max-Age' 1728000;
                add_header 'Content-Type' 'text/plain; charset=utf-8';
                add_header 'Content-Length' 0;
                return 204;
            }        
        }" >> $3
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
            if (\$request_method = 'OPTIONS') {
                add_header 'Access-Control-Allow-Origin' '*';
                add_header 'Access-Control-Allow-Methods' 'GET, POST, DELETE, OPTIONS';
                #
                # Custom headers and headers various browsers *should* be OK with but aren't 
                #
                add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range';
                #
                # Tell client that this pre-flight info is valid for 20 days
                #
                add_header Access-Control-Allow-Headers "Authorization";
                add_header Access-Control-Allow-Credentials "true";
                add_header 'Access-Control-Max-Age' 1728000;
                add_header 'Content-Type' 'text/plain; charset=utf-8';
                add_header 'Content-Length' 0;
                return 204;
            }        
        }" >> $3
}

echo "Platform Name: "
read answer
echo $answer > auth/platform_name
uuidgen > auth/platformID

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

# Allow authentication or not when installin the Dispatcher
while true; do
    read -p "Do you wish to allow Authentication? " yn
    case $yn in
        [Yy]* ) echo "Authentication enabled"; authentication=true; break;;
        [Nn]* ) echo "Authentication disabled"; authentication=false; break;;
        * ) echo "Please answer yes or no.";;
    esac
done

#copy the docker-compose template to the final docker-compose file   
cp docker-compose.tmp docker-compose.yml

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
        if $authentication; then
            add_enabler_auth $module $line $output_file
        else
            add_enabler $module $line $output_file
        fi
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

if $authentication; then
    add_enabler_auth $module $line $output_file
    swagger_file="swagger/template_auth.json"
    echo "
  auth:
    build: ./auth
    image: auth
    container_name: auth
    command: python auth.py
    volumes:
      - \"./auth:/auth\"
    ports:
      - '2000:2000'
    restart: always
" >> docker-compose.yml
else
    add_enabler $module $line $output_file
    swagger_file="swagger/template_no_auth.json"
fi

# Add the local IP to the swagger file
my_ip=$(ip route get 8.8.8.8 | awk -F"src " 'NR==1{split($2,a," ");print a[1]}')
sed "s/DISPATCHER/$my_ip/g" $swagger_file > swagger/swagger.json

echo "Dispatcher configured using information from '$config_file' file"

# after the whole config file is processed, we write the last part of the config file
if $authentication; then
    write_footer_auth $output_file
else
    write_footer $output_file
fi

# Build the images
echo "Building the images..."
docker-compose -f docker-compose.yml build

echo "DONE"
