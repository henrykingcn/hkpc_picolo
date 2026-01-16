/**
 * Animation Controller for Access Control System
 * Manages all visual animations and transitions
 */

class AnimationController {
    constructor() {
        this.isAnimating = false;
        this.animationQueue = [];
    }
    
    /**
     * Play access granted animation sequence
     */
    playAccessGranted(personName) {
        this.isAnimating = true;
        
        // 1. Body parts turn green with ripple effect
        this.animateBodyPartsSuccess();
        
        // 2. Status section transitions
        setTimeout(() => {
            this.transitionStatusSection('granted');
        }, 200);
        
        // 3. Show welcome message with slide-in
        setTimeout(() => {
            this.showWelcomeMessage(personName);
        }, 400);
        
        // 4. Create success particles
        setTimeout(() => {
            this.createSuccessParticles();
        }, 600);
        
        // 5. Start door opening progress
        setTimeout(() => {
            this.animateDoorOpening(3000);
        }, 800);
        
        setTimeout(() => {
            this.isAnimating = false;
        }, 4000);
    }
    
    /**
     * Play access denied animation sequence
     */
    playAccessDenied(reason) {
        this.isAnimating = true;
        
        // 1. Shake the status section
        this.shakeElement('access-status');
        
        // 2. Flash missing PPE parts in red
        setTimeout(() => {
            if (typeof highlightMissingPPE === 'function') {
                highlightMissingPPE();
            }
        }, 200);
        
        // 3. Show denial reason
        setTimeout(() => {
            this.showDenialReason(reason);
        }, 400);
        
        setTimeout(() => {
            this.isAnimating = false;
        }, 2000);
    }
    
    /**
     * Animate body parts turning green
     */
    animateBodyPartsSuccess() {
        const bodyParts = ['head', 'face', 'eyes', 'chest', 'hands-left', 'hands-right', 'feet'];
        
        bodyParts.forEach((partId, index) => {
            setTimeout(() => {
                const part = document.getElementById(partId);
                if (part) {
                    part.style.transition = 'all 0.5s ease';
                    part.classList.add('scale-in');
                    
                    setTimeout(() => {
                        part.classList.remove('scale-in');
                    }, 500);
                }
            }, index * 100);
        });
    }
    
    /**
     * Transition status section with animation
     */
    transitionStatusSection(type) {
        const section = document.getElementById('access-status');
        if (!section) return;
        
        section.classList.add('fade-out');
        
        setTimeout(() => {
            section.classList.remove('fade-out');
            section.classList.add('fade-in');
            
            setTimeout(() => {
                section.classList.remove('fade-in');
            }, 500);
        }, 300);
    }
    
    /**
     * Show welcome message with animation
     */
    showWelcomeMessage(name) {
        const userElement = document.getElementById('status-user');
        if (!userElement) return;
        
        userElement.textContent = `Welcome, ${name}!`;
        userElement.style.display = 'block';
        userElement.classList.add('slide-in-up');
        
        setTimeout(() => {
            userElement.classList.remove('slide-in-up');
        }, 600);
    }
    
    /**
     * Show denial reason with animation
     */
    showDenialReason(reason) {
        const messageElement = document.getElementById('status-message');
        if (!messageElement) return;
        
        messageElement.classList.add('attention-animation');
        
        setTimeout(() => {
            messageElement.classList.remove('attention-animation');
        }, 1000);
    }
    
    /**
     * Create success particles
     */
    createSuccessParticles() {
        const container = document.getElementById('access-status');
        if (!container) return;
        
        const particleCount = 30;
        const colors = ['#10B981', '#34D399', '#6EE7B7', '#FFFFFF'];
        
        for (let i = 0; i < particleCount; i++) {
            setTimeout(() => {
                const particle = document.createElement('div');
                particle.style.position = 'absolute';
                particle.style.width = Math.random() * 10 + 5 + 'px';
                particle.style.height = particle.style.width;
                particle.style.background = colors[Math.floor(Math.random() * colors.length)];
                particle.style.borderRadius = '50%';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.bottom = '0';
                particle.style.pointerEvents = 'none';
                particle.classList.add('particle');
                
                container.appendChild(particle);
                
                setTimeout(() => {
                    particle.remove();
                }, 1500);
            }, i * 50);
        }
    }
    
    /**
     * Animate door opening with progress bar
     */
    animateDoorOpening(duration) {
        const progress = document.getElementById('door-progress');
        const progressBar = document.getElementById('door-progress-bar');
        
        if (!progress || !progressBar) return;
        
        progress.style.display = 'block';
        progressBar.style.width = '0%';
        progressBar.style.transition = 'none';
        
        setTimeout(() => {
            progressBar.style.transition = `width ${duration}ms linear`;
            progressBar.style.width = '100%';
        }, 50);
    }
    
    /**
     * Shake an element
     */
    shakeElement(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.classList.add('shake-animation');
        
        setTimeout(() => {
            element.classList.remove('shake-animation');
        }, 500);
    }
    
    /**
     * Bounce an element
     */
    bounceElement(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.classList.add('bounce-animation');
        
        setTimeout(() => {
            element.classList.remove('bounce-animation');
        }, 600);
    }
    
    /**
     * Flash an element
     */
    flashElement(elementId, color) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const flashClass = color === 'green' ? 'flash-green' : 'flash-red';
        element.classList.add(flashClass);
        
        setTimeout(() => {
            element.classList.remove(flashClass);
        }, 1500);
    }
    
    /**
     * Pulse animation for waiting/checking states
     */
    pulseElement(elementId, enable = true) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        if (enable) {
            element.classList.add('pulse-animation');
        } else {
            element.classList.remove('pulse-animation');
        }
    }
    
    /**
     * Rotate animation (for loading indicators)
     */
    rotateElement(elementId, enable = true) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        if (enable) {
            element.classList.add('rotate-animation');
        } else {
            element.classList.remove('rotate-animation');
        }
    }
    
    /**
     * Clear all animations
     */
    clearAllAnimations() {
        const allElements = document.querySelectorAll('*');
        const animationClasses = [
            'pulse-animation', 'shake-animation', 'bounce-animation',
            'slide-in-up', 'slide-out-down', 'fade-in', 'fade-out',
            'scale-in', 'flash-green', 'flash-red', 'glow-green', 'glow-red',
            'attention-animation', 'rotate-animation', 'blink-animation'
        ];
        
        allElements.forEach(element => {
            animationClasses.forEach(className => {
                element.classList.remove(className);
            });
        });
        
        this.isAnimating = false;
    }
}

// Create global instance
const animationController = new AnimationController();

// Export for use in other scripts
window.animationController = animationController;
window.playAccessGranted = (name) => animationController.playAccessGranted(name);
window.playAccessDenied = (reason) => animationController.playAccessDenied(reason);

console.log('Animation controller initialized');



