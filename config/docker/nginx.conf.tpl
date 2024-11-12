server {

    listen 80 default_server;
    listen [::]:80 default_server;

    access_log  /var/log/nginx/nginx.access.log;
    error_log  /var/log/nginx/nginx.error.log;

    root /tmp;
    index index.html;

    server_name _;

    client_max_body_size        255M;
    proxy_connect_timeout       600;
    proxy_send_timeout          600;
    proxy_read_timeout          600;
    send_timeout                600;

#    location /socket.io {
#
#       proxy_pass socketio_server:5000;
#
#       proxy_redirect off;
#       proxy_set_header Host $host;
#       proxy_set_header X-Real-IP $remote_addr;
#       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#
#       proxy_http_version 1.1;
#       proxy_set_header Upgrade $http_upgrade;
#       proxy_set_header Connection "Upgrade";
#       proxy_read_timeout 3600s;
#
#       proxy_set_header X-Forwarded-Proto $scheme;
#    }

{{services}}

#    location /api/tenants     { proxy_pass http://tenants:8000; proxy_redirect off; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-For $remote_addr; }


    proxy_buffering off;

    rewrite ^/socket.io(.*)$ /socket.io$1 break;
    rewrite ^/api/(.*)$ /api/$1 break;
    rewrite ^/(.*)$ /$1 break;

}