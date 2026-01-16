/**
 * WebSocket Handler for Real-time Access Control Updates
 */

// Initialize Socket.IO connection
const socket = io();

let currentState = 'IDLE';
let currentPerson = null;
let detectedClasses = [];
let requiredClasses = [];

// Connection events
socket.on('connect', () => {
    console.log('✓ Connected to server');
    document.getElementById('system-status').textContent = '● System Active';
    document.getElementById('system-status').style.color = '#10B981';
    
    // Start detection when page connects
    socket.emit('start_detection');
    console.log('🎬 Starting detection...');
});

socket.on('disconnect', () => {
    console.log('✗ Disconnected from server');
    document.getElementById('system-status').textContent = '● Disconnected';
    document.getElementById('system-status').style.color = '#EF4444';
});

// Detection control events
socket.on('detection_started', (data) => {
    console.log('✅ Detection started:', data);
});

socket.on('detection_stopped', (data) => {
    console.log('⏹️ Detection stopped:', data);
});

// Detection update event
socket.on('detection_update', (data) => {
    console.log('Detection update:', data);
    
    // Update detected classes
    detectedClasses = data.detected_classes || [];
    
    // Update body visualization
    if (typeof updateBodyVisualization === 'function') {
        updateBodyVisualization(detectedClasses, requiredClasses);
    }
    
    // Update PPE list
    updatePPEList(data.detected_classes, data.confidence_scores);
});

// Face identification event
socket.on('face_identified', (data) => {
    console.log('Face identified:', data);
    
    currentPerson = data;
    
    const faceStatus = document.getElementById('face-status');
    
    if (data.matched) {
        faceStatus.textContent = `✓ ${data.name} (${(data.confidence * 100).toFixed(1)}%)`;
        faceStatus.style.background = 'rgba(16, 185, 129, 0.8)';
    } else if (data.name === 'Unknown') {
        faceStatus.textContent = '⚠ Unknown Person';
        faceStatus.style.background = 'rgba(239, 68, 68, 0.8)';
    } else {
        faceStatus.textContent = 'Detecting...';
        faceStatus.style.background = 'rgba(0, 0, 0, 0.6)';
    }
});

// Access status change event
socket.on('access_status_change', (data) => {
    console.log('Access status changed:', data);
    
    currentState = data.state;
    
    const statusSection = document.getElementById('access-status');
    const statusIcon = document.getElementById('status-icon');
    const statusText = document.getElementById('status-text');
    const statusMessage = document.getElementById('status-message');
    const statusUser = document.getElementById('status-user');
    const doorProgress = document.getElementById('door-progress');
    
    // Remove all state classes
    statusSection.classList.remove('granted', 'denied', 'checking');
    
    switch (data.state) {
        case 'IDLE':
            statusSection.classList.add('checking');
            statusIcon.textContent = '🔍';
            statusText.textContent = 'READY';
            statusMessage.textContent = 'Please stand in front of camera';
            statusUser.style.display = 'none';
            doorProgress.style.display = 'none';
            break;
            
        case 'FACE_DETECTING':
            statusSection.classList.add('checking');
            statusIcon.textContent = '👤';
            statusText.textContent = 'DETECTING FACE...';
            statusMessage.textContent = 'Please look at the camera';
            statusUser.style.display = 'none';
            doorProgress.style.display = 'none';
            statusIcon.classList.add('pulse-animation');
            break;
            
        case 'FACE_RECOGNIZED':
            statusSection.classList.add('checking');
            statusIcon.textContent = '✓';
            statusText.textContent = 'IDENTITY VERIFIED';
            statusMessage.textContent = 'Checking PPE...';
            statusUser.textContent = `Welcome, ${data.person_name}!`;
            statusUser.style.display = 'block';
            statusUser.classList.add('fade-in');
            doorProgress.style.display = 'none';
            playAnimation('success-beep');
            break;
            
        case 'PPE_CHECKING':
            statusSection.classList.add('checking');
            statusIcon.textContent = '🔎';
            statusText.textContent = 'CHECKING PPE...';
            statusMessage.textContent = data.message || 'Please show required PPE';
            doorProgress.style.display = 'none';
            break;
            
        case 'ACCESS_GRANTED':
            statusSection.classList.add('granted');
            statusIcon.textContent = '✅';
            statusText.textContent = 'ACCESS GRANTED';
            statusMessage.textContent = 'Door opening...';
            statusUser.textContent = `Welcome, ${data.person_name}!`;
            statusUser.style.display = 'block';
            doorProgress.style.display = 'block';
            
            // Animate door progress
            animateDoorProgress(data.duration || 3);
            
            // Play success animation
            playAnimation('access-granted');
            playSuccessAnimation();
            break;
            
        case 'ACCESS_DENIED':
            statusSection.classList.add('denied');
            statusIcon.textContent = '❌';
            statusText.textContent = 'ACCESS DENIED';
            statusMessage.textContent = data.message || 'Access requirements not met';
            
            if (data.person_name) {
                statusUser.textContent = data.person_name;
                statusUser.style.display = 'block';
            } else {
                statusUser.style.display = 'none';
            }
            
            doorProgress.style.display = 'none';
            
            // Play denied animation
            playAnimation('access-denied');
            playDeniedAnimation();
            break;
    }
});

// Config update event
socket.on('config_update', (data) => {
    console.log('Config updated:', data);
    requiredClasses = data.required_classes || [];
    
    // Update visualization with new requirements
    if (typeof updateBodyVisualization === 'function') {
        updateBodyVisualization(detectedClasses, requiredClasses);
    }
});

// Helper function to update PPE list
function updatePPEList(detected, confidence) {
    const ppeList = document.getElementById('ppe-items-list');
    
    if (!requiredClasses || requiredClasses.length === 0) {
        ppeList.innerHTML = '<div style="text-align: center; color: #6B7280;">No PPE requirements configured</div>';
        return;
    }
    
    ppeList.innerHTML = requiredClasses.map(className => {
        const isDetected = detected.some(d => d.toLowerCase() === className.toLowerCase());
        const conf = confidence ? confidence[className] : null;
        
        let statusHTML;
        if (isDetected) {
            const confPercent = conf ? `${(conf * 100).toFixed(0)}%` : '';
            statusHTML = `<span class="ppe-item-status detected">✓ Detected ${confPercent}</span>`;
        } else {
            statusHTML = `<span class="ppe-item-status missing">✗ Missing</span>`;
        }
        
        return `
            <div class="ppe-item">
                <span class="ppe-item-name">${className}</span>
                ${statusHTML}
            </div>
        `;
    }).join('');
}

// Animate door progress bar
function animateDoorProgress(duration) {
    const progressBar = document.getElementById('door-progress-bar');
    progressBar.style.width = '0%';
    progressBar.style.transition = `width ${duration}s linear`;
    
    setTimeout(() => {
        progressBar.style.width = '100%';
    }, 50);
}

// Play sound effects (placeholder for future implementation)
function playAnimation(type) {
    console.log(`Play animation: ${type}`);
    // Could add sound effects here
}

// Success animation with particles
function playSuccessAnimation() {
    const statusSection = document.getElementById('access-status');
    statusSection.classList.add('ripple-effect');
    
    // Create particles
    createParticles(statusSection, 20);
    
    setTimeout(() => {
        statusSection.classList.remove('ripple-effect');
    }, 1000);
}

// Denied animation with shake
function playDeniedAnimation() {
    const statusSection = document.getElementById('access-status');
    statusSection.classList.add('shake-animation');
    
    setTimeout(() => {
        statusSection.classList.remove('shake-animation');
    }, 500);
}

// Create particle effects
function createParticles(container, count) {
    for (let i = 0; i < count; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.bottom = '0';
        particle.style.animationDelay = Math.random() * 0.5 + 's';
        container.appendChild(particle);
        
        setTimeout(() => {
            particle.remove();
        }, 1500);
    }
}

// Request initial configuration
socket.emit('request_config');

// Page lifecycle events
window.addEventListener('beforeunload', function(event) {
    console.log('📴 Page closing/leaving, stopping detection...');
    socket.emit('stop_detection');
});

// Page unload event (backup)
window.addEventListener('unload', function() {
    console.log('📴 Page unloaded, stopping detection...');
    socket.emit('stop_detection');
});

// Handle page visibility changes (tab switching)
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        console.log('👁️ Page hidden (tab switched), stopping detection...');
        socket.emit('stop_detection');
    } else {
        console.log('👁️ Page visible (tab back), restarting detection...');
        socket.emit('start_detection');
    }
});

// Page hide event (navigation away)
window.addEventListener('pagehide', function() {
    console.log('📴 Page hidden (navigation), stopping detection...');
    socket.emit('stop_detection');
});

console.log('WebSocket handler initialized');

