// Service configuration based on dependency graph
const SERVICES = {"user-management": 8000, "course-generator": 8001, "course-management": 8004, "content-storage": 8003};
const SERVICE_URLS = {};

// Initialize service URLs
Object.keys(SERVICES).forEach(service => {
    SERVICE_URLS[service] = `http://localhost:${SERVICES[service]}`;
});

class ServiceHealthMonitor {
    constructor() {
        this.healthStatus = {};
        this.checkInterval = 30000; // 30 seconds
    }
    
    async checkServiceHealth(serviceName) {
        try {
            const response = await fetch(`${SERVICE_URLS[serviceName]}/health`, {
                method: 'GET',
                timeout: 5000
            });
            
            if (response.ok) {
                const health = await response.json();
                this.healthStatus[serviceName] = {
                    status: 'healthy',
                    lastCheck: new Date(),
                    details: health
                };
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            this.healthStatus[serviceName] = {
                status: 'unhealthy',
                lastCheck: new Date(),
                error: error.message
            };
        }
        
        this.updateServiceDisplay(serviceName);
    }
    
    updateServiceDisplay(serviceName) {
        const element = document.querySelector(`[data-service="${serviceName}"] .service-status`);
        if (element) {
            const status = this.healthStatus[serviceName];
            element.textContent = status.status;
            element.className = `service-status ${status.status}`;
        }
    }
    
    startMonitoring() {
        // Initial check
        Object.keys(SERVICES).forEach(service => {
            this.checkServiceHealth(service);
        });
        
        // Periodic checks
        setInterval(() => {
            Object.keys(SERVICES).forEach(service => {
                this.checkServiceHealth(service);
            });
        }, this.checkInterval);
    }
}

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    const healthMonitor = new ServiceHealthMonitor();
    
    // Start health monitoring
    healthMonitor.startMonitoring();
    
    // Navigation handling
    document.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = this.getAttribute('href').substring(1);
            showSection(target);
        });
    });
    
    function showSection(sectionId) {
        document.querySelectorAll('main section').forEach(section => {
            section.style.display = 'none';
        });
        
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.style.display = 'block';
        }
    }
    
    console.log('Course Creator Platform loaded with dependency graph integration');
});