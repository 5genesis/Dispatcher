import configparser

header = """
events {
    worker_connections  1024;  ## Default: 1024
}

http {
    log_format   main '$remote_addr - $remote_user [$time_local]  $status '
        '"$request" $body_bytes_sent "$http_referer" '
        '"$http_user_agent" "$http_x_forwarded_for"';
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
                          }"""

auth = """

        location /auth {
            proxy_pass http://auth:2000/;
            #rewrite ^/(.*)/$ /$1 permanent;
            proxy_redirect     off;
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Host $server_name;
            if ($request_method = 'OPTIONS') {
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
                add_header Access-Control-Allow-Headers Authorization;
                add_header Access-Control-Allow-Credentials true;
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
            proxy_set_header        Content-Length "";
            proxy_set_header        X-Original-URI $request_uri;
        }
    }
}"""

add_enabler = """

        location /{0} {
            auth_request     /mandatory_auth;
            auth_request_set $auth_status $upstream_status;
            proxy_pass {1};
            #rewrite ^/(.*)/$ /$1 permanent;
            proxy_redirect     off;
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Host $server_name;
            if ($request_method = 'OPTIONS') {
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
                add_header Access-Control-Allow-Headers Authorization;
                add_header Access-Control-Allow-Credentials true;
                add_header 'Access-Control-Max-Age' 1728000;
                add_header 'Content-Type' 'text/plain; charset=utf-8';
                add_header 'Content-Length' 0;
                return 204;
            }
        }"""



conf = configparser.ConfigParser()
configFilePath = r'dispatcher.conf'
conf.read(configFilePath)
enablers = ""
for sect in conf.sections():
    url = conf[sect]['protocol'] + '://' + conf[sect]['host'] + ':' + conf[sect]['port'] + conf[sect]['path']
    enablers += add_enabler.replace("{0}", sect).replace("{1}", url)

with open('nginx.conf', 'w') as file:
    file.write(header+enablers+auth)
