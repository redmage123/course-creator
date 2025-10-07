# Frontend Service Dockerfile
FROM nginx:alpine

# Copy static files to nginx html directory with proper structure
COPY . /usr/share/nginx/html/

# Remove nginx default files first
RUN rm -f /usr/share/nginx/html/index.html /usr/share/nginx/html/50x.html

# Copy Course Creator index.html to root and verify
RUN cp /usr/share/nginx/html/html/index.html /usr/share/nginx/html/index.html && \
    ls -la /usr/share/nginx/html/index.html && \
    head -3 /usr/share/nginx/html/index.html

# Fix permissions for public directory
RUN chmod -R 755 /usr/share/nginx/html/public

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create SSL directory and copy certificates
RUN mkdir -p /etc/nginx/ssl
COPY ssl/nginx-selfsigned.crt /etc/nginx/ssl/
COPY ssl/nginx-selfsigned.key /etc/nginx/ssl/

# Create non-root user for security
RUN addgroup -g 1001 -S nginx-user && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx-user -g nginx-user nginx-user

# Expose ports
EXPOSE 3000

# Health check (updated for HTTPS)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider --no-check-certificate https://127.0.0.1:3000/health || exit 1

# Run nginx
CMD ["nginx", "-g", "daemon off;"]