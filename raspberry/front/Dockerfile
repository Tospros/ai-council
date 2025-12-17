FROM nginx:alpine
COPY front/ /usr/share/nginx/html/
COPY front/nginx.conf /etc/nginx/conf.d/default.conf
COPY front/99-gen-config.sh /docker-entrypoint.d/99-gen-config.sh
RUN chmod +x /docker-entrypoint.d/99-gen-config.sh
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
