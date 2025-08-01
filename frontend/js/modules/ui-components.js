/**
 * UI Components Module
 * Reusable UI components and utilities
 */

export class UIComponents {
    /**
     * Create a modal dialog
     */
    static createModal(title, content, options = {}) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">${title}</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                ${options.footer ? `<div class="modal-footer">${options.footer}</div>` : ''}
            </div>
        `;
        
        // Add event listener for backdrop clicks
        modal.addEventListener('click', (e) => {
            if (e.target === modal && !options.disableBackdropClose) {
                modal.remove();
            }
        });
        
        // Add styles if not already present
        if (!document.getElementById('modal-styles')) {
            const style = document.createElement('style');
            style.id = 'modal-styles';
            style.textContent = `
                .modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 10000;
                    backdrop-filter: blur(2px);
                }
                
                .modal-content {
                    background: white;
                    border-radius: 12px;
                    max-width: 500px;
                    width: 90%;
                    max-height: 90vh;
                    overflow-y: auto;
                    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
                    animation: modalSlideIn 0.3s ease;
                }
                
                @keyframes modalSlideIn {
                    from {
                        transform: translateY(-50px);
                        opacity: 0;
                    }
                    to {
                        transform: translateY(0);
                        opacity: 1;
                    }
                }
                
                .modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 20px;
                    border-bottom: 1px solid #eee;
                }
                
                .modal-title {
                    margin: 0;
                    font-size: 18px;
                    font-weight: 600;
                    color: #333;
                }
                
                .modal-close {
                    background: none;
                    border: none;
                    font-size: 24px;
                    cursor: pointer;
                    color: #666;
                    padding: 0;
                    width: 30px;
                    height: 30px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 50%;
                    transition: all 0.2s ease;
                }
                
                .modal-close:hover {
                    background: #f5f5f5;
                    color: #333;
                }
                
                .modal-body {
                    padding: 20px;
                }
                
                .modal-footer {
                    padding: 20px;
                    border-top: 1px solid #eee;
                    display: flex;
                    justify-content: flex-end;
                    gap: 12px;
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(modal);
        return modal;
    }

    /**
     * Create a loading spinner
     */
    static createLoadingSpinner(text = 'Loading...') {
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        
        spinner.innerHTML = `
            <div class="spinner-animation"></div>
            <div class="spinner-text">${text}</div>
        `;
        
        // Add styles if not already present
        if (!document.getElementById('spinner-styles')) {
            const style = document.createElement('style');
            style.id = 'spinner-styles';
            style.textContent = `
                .loading-spinner {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                    color: #666;
                }
                
                .spinner-animation {
                    width: 32px;
                    height: 32px;
                    border: 3px solid #f3f3f3;
                    border-top: 3px solid #3498db;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-bottom: 12px;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                .spinner-text {
                    font-size: 14px;
                    color: #666;
                }
            `;
            document.head.appendChild(style);
        }
        
        return spinner;
    }

    /**
     * Create a toggle password visibility button
     */
    static createPasswordToggle(inputId) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'password-toggle';
        button.innerHTML = '👁️';
        button.title = 'Show password';
        
        button.addEventListener('click', () => {
            const input = document.getElementById(inputId);
            if (input) {
                if (input.type === 'password') {
                    input.type = 'text';
                    button.innerHTML = '🙈';
                    button.title = 'Hide password';
                } else {
                    input.type = 'password';
                    button.innerHTML = '👁️';
                    button.title = 'Show password';
                }
            }
        });
        
        // Add styles if not already present
        if (!document.getElementById('password-toggle-styles')) {
            const style = document.createElement('style');
            style.id = 'password-toggle-styles';
            style.textContent = `
                .password-toggle {
                    position: absolute;
                    right: 8px;
                    top: 50%;
                    transform: translateY(-50%);
                    background: none;
                    border: none;
                    cursor: pointer;
                    font-size: 16px;
                    color: #666;
                    padding: 4px;
                    border-radius: 4px;
                    transition: all 0.2s ease;
                }
                
                .password-toggle:hover {
                    background: #f5f5f5;
                    color: #333;
                }
                
                .password-input-container {
                    position: relative;
                    display: inline-block;
                    width: 100%;
                }
                
                .password-input-container input {
                    padding-right: 40px;
                }
            `;
            document.head.appendChild(style);
        }
        
        return button;
    }

    /**
     * Create a dropdown menu
     */
    static createDropdown(trigger, items, options = {}) {
        const dropdown = document.createElement('div');
        dropdown.className = 'dropdown';
        
        const menu = document.createElement('div');
        menu.className = 'dropdown-menu';
        
        items.forEach(item => {
            const menuItem = document.createElement('div');
            menuItem.className = 'dropdown-item';
            
            if (typeof item === 'string') {
                menuItem.textContent = item;
            } else {
                menuItem.innerHTML = item.html || item.text;
                if (item.onclick) {
                    menuItem.addEventListener('click', item.onclick);
                }
                if (item.href) {
                    menuItem.style.cursor = 'pointer';
                    menuItem.addEventListener('click', () => {
                        window.location.href = item.href;
                    });
                }
            }
            
            menu.appendChild(menuItem);
        });
        
        dropdown.appendChild(trigger);
        dropdown.appendChild(menu);
        
        // Toggle dropdown on trigger click
        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            menu.classList.toggle('show');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            menu.classList.remove('show');
        });
        
        // Add styles if not already present
        if (!document.getElementById('dropdown-styles')) {
            const style = document.createElement('style');
            style.id = 'dropdown-styles';
            style.textContent = `
                .dropdown {
                    position: relative;
                    display: inline-block;
                }
                
                .dropdown-menu {
                    position: absolute;
                    top: 100%;
                    right: 0;
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    min-width: 200px;
                    z-index: 1000;
                    opacity: 0;
                    visibility: hidden;
                    transform: translateY(-10px);
                    transition: all 0.2s ease;
                }
                
                .dropdown-menu.show {
                    opacity: 1;
                    visibility: visible;
                    transform: translateY(0);
                }
                
                .dropdown-item {
                    padding: 12px 16px;
                    cursor: pointer;
                    transition: background-color 0.2s ease;
                    border-bottom: 1px solid #f5f5f5;
                }
                
                .dropdown-item:last-child {
                    border-bottom: none;
                }
                
                .dropdown-item:hover {
                    background-color: #f8f9fa;
                }
                
                .dropdown-item:first-child {
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                }
                
                .dropdown-item:last-child {
                    border-bottom-left-radius: 8px;
                    border-bottom-right-radius: 8px;
                }
            `;
            document.head.appendChild(style);
        }
        
        return dropdown;
    }

    /**
     * Create a confirmation dialog
     */
    static createConfirmDialog(message, onConfirm, onCancel) {
        const footer = `
            <button type="button" class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
            <button type="button" class="btn btn-primary" id="confirm-btn">Confirm</button>
        `;
        
        const modal = this.createModal('Confirm Action', `<p>${message}</p>`, { footer });
        
        const confirmBtn = modal.querySelector('#confirm-btn');
        confirmBtn.addEventListener('click', () => {
            if (onConfirm) onConfirm();
            modal.remove();
        });
        
        const cancelBtn = modal.querySelector('.btn-secondary');
        cancelBtn.addEventListener('click', () => {
            if (onCancel) onCancel();
        });
        
        return modal;
    }

    /**
     * Create a form field with validation
     */
    static createFormField(config) {
        const field = document.createElement('div');
        field.className = 'form-field';
        
        const label = document.createElement('label');
        label.textContent = config.label;
        label.setAttribute('for', config.id);
        
        const input = document.createElement(config.type || 'input');
        input.id = config.id;
        input.name = config.name || config.id;
        
        if (config.type === 'input') {
            input.type = config.inputType || 'text';
        }
        
        if (config.placeholder) {
            input.placeholder = config.placeholder;
        }
        
        if (config.required) {
            input.required = true;
        }
        
        if (config.validation) {
            input.addEventListener('input', () => {
                const isValid = config.validation(input.value);
                if (isValid === true) {
                    input.classList.remove('error');
                    input.classList.add('valid');
                } else {
                    input.classList.remove('valid');
                    input.classList.add('error');
                }
            });
        }
        
        field.appendChild(label);
        
        if (config.inputType === 'password') {
            const container = document.createElement('div');
            container.className = 'password-input-container';
            container.appendChild(input);
            container.appendChild(this.createPasswordToggle(config.id));
            field.appendChild(container);
        } else {
            field.appendChild(input);
        }
        
        return field;
    }

    /**
     * Get user initials for avatar
     */
    static getInitials(name) {
        if (!name) return 'U';
        
        const words = name.split(' ');
        if (words.length >= 2) {
            return (words[0][0] + words[1][0]).toUpperCase();
        } else {
            return name.substring(0, 2).toUpperCase();
        }
    }

    /**
     * Create user avatar
     */
    static createAvatar(user, size = 'medium') {
        const avatar = document.createElement('div');
        avatar.className = `user-avatar ${size}`;
        
        const initials = this.getInitials(user.full_name || user.username || user.email);
        avatar.textContent = initials;
        
        // Set background color based on role
        if (user.role === 'admin') {
            avatar.style.background = 'linear-gradient(45deg, #e74c3c, #c0392b)';
        } else if (user.role === 'instructor') {
            avatar.style.background = 'linear-gradient(45deg, #f39c12, #e67e22)';
        } else {
            avatar.style.background = 'linear-gradient(45deg, #3498db, #2980b9)';
        }
        
        // Add styles if not already present
        if (!document.getElementById('avatar-styles')) {
            const style = document.createElement('style');
            style.id = 'avatar-styles';
            style.textContent = `
                .user-avatar {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 50%;
                    color: white;
                    font-weight: 600;
                    text-transform: uppercase;
                    background: linear-gradient(45deg, #3498db, #2980b9);
                }
                
                .user-avatar.small {
                    width: 24px;
                    height: 24px;
                    font-size: 10px;
                }
                
                .user-avatar.medium {
                    width: 32px;
                    height: 32px;
                    font-size: 12px;
                }
                
                .user-avatar.large {
                    width: 48px;
                    height: 48px;
                    font-size: 16px;
                }
                
                .user-avatar.xlarge {
                    width: 80px;
                    height: 80px;
                    font-size: 24px;
                }
            `;
            document.head.appendChild(style);
        }
        
        return avatar;
    }

    /**
     * Format date for display
     */
    static formatDate(date, options = {}) {
        const d = new Date(date);
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        
        return d.toLocaleDateString('en-US', { ...defaultOptions, ...options });
    }

    /**
     * Debounce function
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Throttle function
     */
    static throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

export default UIComponents;