#!/bin/bash
# Simple wrapper to deploy ansible playbooks on skvo server
# You need to be root 

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

echo "Deploying $PLAY_DEPLOY ..."
ansible-playbook -i inventory/skvo_env $@ $PLAY_DEPLOY -vv
