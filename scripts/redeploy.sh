reload_nginx() {  
  docker exec pms_proxy_1 /usr/sbin/nginx -s reload  
}
