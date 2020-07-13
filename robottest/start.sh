#!/bin/bash

sed 's@\/home@'"$ROBOT_RESULTS_DIR"'@g' /etc/lighttpd/lighttpd.conf > /etc/lighttpd/lighttpd.conf2 && mv /etc/lighttpd/lighttpd.conf2 /etc/lighttpd/lighttpd.conf && service lighttpd restart
#source environment.rc

/bin/bash

