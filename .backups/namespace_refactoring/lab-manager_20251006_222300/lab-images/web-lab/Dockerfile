# Web Development Lab Environment (HTML/CSS/JS)
FROM nginx:alpine

# Install Node.js for build tools
RUN apk add --no-cache \
    nodejs \
    npm \
    git \
    curl \
    nano \
    vim

# Install global web development tools
RUN npm install -g \
    live-server \
    browser-sync \
    sass \
    less \
    postcss-cli \
    autoprefixer \
    typescript \
    webpack \
    webpack-cli \
    webpack-dev-server

# Create lab user
RUN addgroup -g 1001 -S labuser && \
    adduser -S -D -H -u 1001 -h /home/labuser -s /bin/sh -G labuser -g labuser labuser

# Set up workspace
RUN mkdir -p /home/labuser/workspace
WORKDIR /home/labuser/workspace

# Create default web lab structure
RUN mkdir -p /home/labuser/workspace/{assignments,solutions,projects,assets/{css,js,images}}

# Copy lab startup script
COPY lab-startup.sh /home/labuser/lab-startup.sh
COPY nginx-lab.conf /etc/nginx/conf.d/default.conf

# Set permissions
RUN chown -R labuser:labuser /home/labuser
RUN chmod +x /home/labuser/lab-startup.sh

# Switch to lab user for file operations
USER labuser

# Create welcome page and starter files
RUN echo '<!DOCTYPE html>\
<html lang="en">\
<head>\
    <meta charset="UTF-8">\
    <meta name="viewport" content="width=device-width, initial-scale=1.0">\
    <title>Web Development Lab</title>\
    <link rel="stylesheet" href="assets/css/style.css">\
</head>\
<body>\
    <header>\
        <h1>🌐 Web Development Lab</h1>\
        <p>HTML, CSS, and JavaScript Learning Environment</p>\
    </header>\
    <main>\
        <section class="welcome">\
            <h2>Welcome to Your Web Lab!</h2>\
            <p>This environment provides everything you need for front-end web development.</p>\
        </section>\
        <section class="features">\
            <h2>Available Tools</h2>\
            <div class="feature-grid">\
                <div class="feature">HTML5</div>\
                <div class="feature">CSS3</div>\
                <div class="feature">JavaScript ES6+</div>\
                <div class="feature">Sass/SCSS</div>\
                <div class="feature">Live Reload</div>\
                <div class="feature">Responsive Design</div>\
            </div>\
        </section>\
    </main>\
    <script src="assets/js/app.js"></script>\
</body>\
</html>' > /home/labuser/workspace/index.html

# Create CSS file
RUN echo '/* Web Lab Styles */\
* { margin: 0; padding: 0; box-sizing: border-box; }\
body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }\
header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-align: center; padding: 2rem; }\
main { max-width: 1200px; margin: 0 auto; padding: 2rem; }\
.welcome { background: #f8f9fa; padding: 2rem; border-radius: 8px; margin-bottom: 2rem; }\
.features h2 { margin-bottom: 1rem; }\
.feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }\
.feature { background: #e9ecef; padding: 1rem; border-radius: 5px; text-align: center; font-weight: bold; }' > /home/labuser/workspace/assets/css/style.css

# Create JavaScript file
RUN echo 'console.log("Web Development Lab loaded!");\
document.addEventListener("DOMContentLoaded", function() {\
    const features = document.querySelectorAll(".feature");\
    features.forEach((feature, index) => {\
        feature.style.animationDelay = (index * 0.1) + "s";\
        feature.classList.add("fade-in");\
    });\
});' > /home/labuser/workspace/assets/js/app.js

# Switch back to root for nginx
USER root

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Start nginx and lab environment
CMD ["/home/labuser/lab-startup.sh"]