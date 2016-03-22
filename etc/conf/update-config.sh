#!/bin/bash
set -x

APP=ichair
HOST=qubit

NGINX_CONF_FILE=$APP-nginx-$HOST.conf
NGINX_AVAILABLE_DIR=/etc/nginx/sites-available
NGINX_ENABLED_DIR=/etc/nginx/sites-enabled

SVISOR_CONF_FILE=$APP-supervisor-$HOST.conf
SVISOR_CONF_DIR=/etc/supervisor/conf.d

cp $NGINX_CONF_FILE $NGINX_AVAILABLE_DIR
ln -s $NGINX_AVAILABLE_DIR/$NGINX_CONF_FILE $NGINX_ENABLED_DIR

cp $SVISOR_CONF_FILE $SVISOR_CONF_DIR
