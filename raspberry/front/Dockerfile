FROM nginx:alpine

# Skopiuj pliki frontendu
COPY front/ /usr/share/nginx/html/

# Skopiuj konfigurację nginx
COPY front/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
