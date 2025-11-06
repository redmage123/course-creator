/**
 * Data Visualization Manager
 * Modern charts, analytics, and interactive data displays
 */
class DataVisualization {
    /**
     * INITIALIZE CLASS INSTANCE WITH DEFAULT STATE
     * PURPOSE: Initialize class instance with default state
     * WHY: Establishes initial state required for class functionality
     */
    constructor() {
        this.charts = new Map();
        this.animationDuration = 1000;
        this.colors = {
            primary: '#6366f1',
            success: '#10b981',
            warning: '#f59e0b',
            danger: '#ef4444',
            info: '#06b6d4',
            gradients: {
                primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                success: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                warning: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
                cool: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)'
            }
        };
        
        this.init();
    }

    /**
     * Initialize data visualization system
     */
    init() {
        this.createSVGDefinitions();
        console.log('Data Visualization Manager initialized');
    }

    /**
     * Create SVG gradient definitions
     */
    createSVGDefinitions() {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.style.position = 'absolute';
        svg.style.width = '0';
        svg.style.height = '0';
        
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        
        // Progress ring gradient
        const progressGradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
        progressGradient.id = 'progressGradient';
        progressGradient.innerHTML = `
            <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
        `;
        
        defs.appendChild(progressGradient);
        svg.appendChild(defs);
        document.body.appendChild(svg);
    }

    /**
     * Create modern stat card with trend
     */
    createStatCard(container, data) {
        const { title, value, trend, trendValue, icon, description, miniChart } = data;
        
        const trendClass = trend > 0 ? 'positive' : trend < 0 ? 'negative' : 'neutral';
        const trendIcon = trend > 0 ? 'fa-arrow-up' : trend < 0 ? 'fa-arrow-down' : 'fa-minus';
        
        const cardHTML = `
            <div class="modern-stat-card" role="region" aria-labelledby="stat-${title.replace(/\s+/g, '-').toLowerCase()}">
                <div class="stat-card-header">
                    <div class="stat-card-icon" aria-hidden="true">
                        <i class="${icon}"></i>
                    </div>
                    <div class="stat-card-trend ${trendClass}" aria-label="Trend: ${trendValue}">
                        <i class="fas ${trendIcon}" aria-hidden="true"></i>
                        <span>${Math.abs(trendValue)}%</span>
                    </div>
                </div>
                <div class="stat-card-value" id="stat-${title.replace(/\s+/g, '-').toLowerCase()}" aria-live="polite">
                    ${value}
                </div>
                <div class="stat-card-label">${title}</div>
                ${description ? `<div class="stat-card-description">${description}</div>` : ''}
                ${miniChart ? this.createMiniChart(miniChart) : ''}
            </div>
        `;
        
        if (typeof container === 'string') {
            container = document.getElementById(container);
        }
        
        if (container) {
            container.innerHTML = cardHTML;
            
            // Animate value counter
            this.animateCounter(container.querySelector('.stat-card-value'), value);
        }
        
        return container;
    }

    /**
     * Create mini chart for stat cards
     */
    createMiniChart(data) {
        const percentage = Math.max(0, Math.min(100, data.percentage || 75));
        
        return `
            <div class="stat-card-mini-chart" aria-label="Progress: ${percentage}%">
                <div class="mini-chart-bar" style="width: ${percentage}%"></div>
            </div>
        `;
    }

    /**
     * Create progress ring chart
     */
    createProgressRing(container, data) {
        const { value, max = 100, label, color = this.colors.primary } = data;
        const percentage = Math.max(0, Math.min(100, (value / max) * 100));
        const radius = 50;
        const circumference = 2 * Math.PI * radius;
        const strokeDasharray = circumference;
        const strokeDashoffset = circumference - (percentage / 100) * circumference;
        
        const ringHTML = `
            <div class="progress-ring-container" role="progressbar" aria-valuenow="${value}" aria-valuemax="${max}" aria-label="${label}: ${value} of ${max}">
                <svg class="progress-ring" viewBox="0 0 120 120">
                    <circle class="progress-ring-track" cx="60" cy="60" r="${radius}"></circle>
                    <circle class="progress-ring-progress" 
                            cx="60" cy="60" r="${radius}"
                            stroke-dasharray="${strokeDasharray}"
                            stroke-dashoffset="${strokeDashoffset}">
                    </circle>
                </svg>
                <div class="progress-ring-text">
                    <span class="progress-ring-value">${Math.round(percentage)}%</span>
                    <span class="progress-ring-label">${label}</span>
                </div>
            </div>
        `;
        
        if (typeof container === 'string') {
            container = document.getElementById(container);
        }
        
        if (container) {
            container.innerHTML = ringHTML;
            
            // Animate progress ring
            setTimeout(() => {
                const progressCircle = container.querySelector('.progress-ring-progress');
                if (progressCircle) {
                    progressCircle.style.strokeDashoffset = strokeDashoffset;
                }
            }, 100);
        }
        
        return container;
    }

    /**
     * Create enhanced data table with visualizations
     */
    createDataTable(container, data) {
        const { title, columns, rows, actions = [] } = data;
        
        const actionsHTML = actions.map(action => 
            `<button class="table-action-btn" onclick="${action.onclick}" aria-label="${action.label}">
                <i class="${action.icon}" aria-hidden="true"></i> ${action.label}
            </button>`
        ).join('');
        
        const headersHTML = columns.map(col => 
            `<th scope="col" aria-sort="none">${col.label}</th>`
        ).join('');
        
        const rowsHTML = rows.map(row => {
            const cellsHTML = columns.map(col => {
                const cellValue = row[col.key];
                
                if (col.type === 'chart') {
                    const percentage = Math.max(0, Math.min(100, cellValue));
                    return `<td>
                        <div class="table-cell-chart" style="--width: ${percentage}%" aria-label="${percentage}%"></div>
                        <span class="sr-only">${percentage}%</span>
                    </td>`;
                } else if (col.type === 'badge') {
                    const badgeClass = this.getBadgeClass(cellValue);
                    return `<td><span class="status-badge ${badgeClass}">${cellValue}</span></td>`;
                } else if (col.type === 'trend') {
                    const trendClass = cellValue > 0 ? 'positive' : cellValue < 0 ? 'negative' : 'neutral';
                    const trendIcon = cellValue > 0 ? 'fa-arrow-up' : cellValue < 0 ? 'fa-arrow-down' : 'fa-minus';
                    return `<td>
                        <span class="stat-card-trend ${trendClass}">
                            <i class="fas ${trendIcon}" aria-hidden="true"></i>
                            ${Math.abs(cellValue)}%
                        </span>
                    </td>`;
                } else {
                    return `<td>${cellValue}</td>`;
                }
            }).join('');
            
            return `<tr>${cellsHTML}</tr>`;
        }).join('');
        
        const tableHTML = `
            <div class="data-visualization-table">
                <div class="data-table-header">
                    <h3 class="data-table-title">${title}</h3>
                    <div class="data-table-actions">
                        ${actionsHTML}
                    </div>
                </div>
                <div style="overflow-x: auto;">
                    <table class="enhanced-data-table" role="table" aria-label="${title}">
                        <thead>
                            <tr>${headersHTML}</tr>
                        </thead>
                        <tbody>
                            ${rowsHTML}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        if (typeof container === 'string') {
            container = document.getElementById(container);
        }
        
        if (container) {
            container.innerHTML = tableHTML;
            this.enhanceTableAccessibility(container);
        }
        
        return container;
    }

    /**
     * Create activity timeline
     */
    createActivityTimeline(container, activities) {
        const timelineHTML = activities.map(activity => `
            <div class="timeline-item">
                <div class="timeline-content">
                    <div class="timeline-header">
                        <h4 class="timeline-title">${activity.title}</h4>
                        <time class="timeline-time" datetime="${activity.timestamp}">
                            ${this.formatTimeAgo(activity.timestamp)}
                        </time>
                    </div>
                    <p class="timeline-description">${activity.description}</p>
                </div>
            </div>
        `).join('');
        
        const fullHTML = `
            <div class="activity-timeline" role="region" aria-label="Activity Timeline">
                ${timelineHTML}
            </div>
        `;
        
        if (typeof container === 'string') {
            container = document.getElementById(container);
        }
        
        if (container) {
            container.innerHTML = fullHTML;
        }
        
        return container;
    }

    /**
     * Create heatmap visualization
     */
    createHeatmap(container, data) {
        const { title, data: heatmapData, maxValue } = data;
        
        const cellsHTML = heatmapData.map(value => {
            const intensity = Math.ceil((value / maxValue) * 5);
            return `<div class="heatmap-cell intensity-${intensity}" 
                         data-value="${value}" 
                         aria-label="Value: ${value}"
                         title="Activity level: ${value}"></div>`;
        }).join('');
        
        const heatmapHTML = `
            <div class="heatmap-container">
                <h4>${title}</h4>
                <div class="heatmap-grid" role="img" aria-label="${title} heatmap">
                    ${cellsHTML}
                </div>
            </div>
        `;
        
        if (typeof container === 'string') {
            container = document.getElementById(container);
        }
        
        if (container) {
            container.innerHTML = heatmapHTML;
        }
        
        return container;
    }

    /**
     * Create chart with loading state
     */
    createChartContainer(container, config) {
        const { title, type, controls = [] } = config;
        
        const controlsHTML = controls.map(control => 
            `<button class="chart-period-selector" data-period="${control.value}" onclick="${control.onclick}">
                ${control.label}
            </button>`
        ).join('');
        
        const chartHTML = `
            <div class="chart-container">
                <div class="chart-header">
                    <h3 class="chart-title">
                        <i class="${config.icon || 'fas fa-chart-line'}" aria-hidden="true"></i>
                        ${title}
                    </h3>
                    <div class="chart-controls">
                        ${controlsHTML}
                    </div>
                </div>
                <div class="chart-content" id="${container}-content">
                    <div class="chart-loading">
                        <div class="loading-spinner"></div>
                        <p>Loading chart data...</p>
                    </div>
                </div>
            </div>
        `;
        
        if (typeof container === 'string') {
            container = document.getElementById(container);
        }
        
        if (container) {
            container.innerHTML = chartHTML;
        }
        
        return container;
    }

    /**
     * Show chart loading state
     */
    showChartLoading(containerId) {
        const content = document.getElementById(`${containerId}-content`);
        if (content) {
            content.innerHTML = `
                <div class="chart-loading">
                    <div class="loading-spinner"></div>
                    <p>Loading chart data...</p>
                </div>
            `;
        }
    }

    /**
     * Create skeleton loading for charts
     */
    createChartSkeleton(height = '200px') {
        return `
            <div class="chart-skeleton" style="height: ${height}; margin: 1rem 0;"></div>
        `;
    }

    /**
     * Animate counter values
     */
    animateCounter(element, targetValue) {
        if (!element) return;
        
        const isNumber = !isNaN(targetValue);
        if (!isNumber) {
            element.textContent = targetValue;
            return;
        }
        
        const startValue = 0;
        const duration = this.animationDuration;
        const startTime = performance.now();
        
    /**
     * EXECUTE ANIMATE OPERATION
     * PURPOSE: Execute animate operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} currentTime - Currenttime parameter
     */
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function for smooth animation
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const currentValue = Math.floor(startValue + (targetValue - startValue) * easeOut);
            
            element.textContent = currentValue.toLocaleString();
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.textContent = targetValue.toLocaleString();
            }
        };
        
        requestAnimationFrame(animate);
    }

    /**
     * Get badge class based on status
     */
    getBadgeClass(status) {
        const statusLower = status.toLowerCase();
        if (['active', 'success', 'completed', 'online'].includes(statusLower)) {
            return 'active';
        } else if (['inactive', 'error', 'failed', 'offline'].includes(statusLower)) {
            return 'inactive';
        } else {
            return 'pending';
        }
    }

    /**
     * Enhance table accessibility
     */
    enhanceTableAccessibility(container) {
        const table = container.querySelector('table');
        const headers = table.querySelectorAll('th');
        const rows = table.querySelectorAll('tbody tr');
        
        // Add sorting capabilities
        headers.forEach((header, index) => {
            header.style.cursor = 'pointer';
            header.setAttribute('tabindex', '0');
            
    /**
     * HANDLE SORT EVENT
     * PURPOSE: Handle sort event
     * WHY: Encapsulates event handling logic for better code organization
     */
            const handleSort = () => {
                const currentSort = header.getAttribute('aria-sort');
                const newSort = currentSort === 'ascending' ? 'descending' : 'ascending';
                
                // Reset all headers
                headers.forEach(h => h.setAttribute('aria-sort', 'none'));
                header.setAttribute('aria-sort', newSort);
                
                // Sort table rows (simplified implementation)
                this.sortTableRows(table, index, newSort === 'ascending');
                
                // Announce sort change
                if (window.a11y) {
                    window.a11y.announce(`Table sorted by ${header.textContent} ${newSort}`);
                }
            };
            
            header.addEventListener('click', handleSort);
            header.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleSort();
                }
            });
        });
    }

    /**
     * Sort table rows (simplified implementation)
     */
    sortTableRows(table, columnIndex, ascending) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        rows.sort((a, b) => {
            const aValue = a.cells[columnIndex].textContent.trim();
            const bValue = b.cells[columnIndex].textContent.trim();
            
            // Try to parse as numbers
            const aNum = parseFloat(aValue.replace(/[^0-9.-]/g, ''));
            const bNum = parseFloat(bValue.replace(/[^0-9.-]/g, ''));
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return ascending ? aNum - bNum : bNum - aNum;
            } else {
                return ascending ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
            }
        });
        
        // Re-append rows in new order
        rows.forEach(row => tbody.appendChild(row));
    }

    /**
     * Format time ago
     */
    formatTimeAgo(timestamp) {
        const now = new Date();
        const date = new Date(timestamp);
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) {
            return 'Just now';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else {
            const days = Math.floor(diffInSeconds / 86400);
            return `${days} day${days > 1 ? 's' : ''} ago`;
        }
    }

    /**
     * Update chart data with animation
     */
    updateChartData(chartId, newData) {
        const chart = this.charts.get(chartId);
        if (chart) {
            // Implement chart update logic based on chart type
            console.log(`Updating chart ${chartId} with new data:`, newData);
        }
    }

    /**
     * Destroy chart and clean up
     */
    destroyChart(chartId) {
        const chart = this.charts.get(chartId);
        if (chart) {
            // Clean up chart instance
            this.charts.delete(chartId);
        }
    }
}

// Create global data visualization instance
window.dataViz = new DataVisualization();

// Export for ES6 modules
export { DataVisualization };
export default DataVisualization;