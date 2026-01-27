FROM nginx:alpine

# Copy static files
COPY front/index.html /usr/share/nginx/html/
COPY front/style.css /usr/share/nginx/html/
COPY front/app.js /usr/share/nginx/html/

# Copy nginx configuration
COPY front/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
