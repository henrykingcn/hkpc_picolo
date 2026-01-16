/**
 * Body Visualization Handler
 * Updates SVG body parts based on PPE detection
 */

// Body part to PPE class mapping
const BODY_PART_MAPPING = {
    'head': ['Head', 'Helmet'],
    'face': ['Face', 'Face-mask-medical'],
    'eyes': ['Glasses', 'Face-guard'],
    'mouth': ['Face-mask-medical'],
    'ears': ['Ear', 'Earmuffs'],
    'chest': ['Safety-vest', 'Medical-suit', 'Safety-suit'],
    'hands-left': ['Hands', 'Gloves'],
    'hands-right': ['Hands', 'Gloves'],
    'feet': ['Foot', 'Shoes']
};

// Color codes for different states
const COLORS = {
    REQUIRED_DETECTED: '#10B981',     // Green
    REQUIRED_MISSING: '#EF4444',      // Red
    NOT_REQUIRED: '#9CA3AF',          // Gray
    CHECKING: '#F59E0B',              // Yellow
    DEFAULT: '#D1D5DB'                // Light Gray
};

let svgLoaded = false;
let currentDetected = [];
let currentRequired = [];

/**
 * Initialize body visualization
 */
function initBodyVisualization() {
    console.log('Initializing body visualization...');
    svgLoaded = true;
    
    // Add transition classes to all body parts
    Object.keys(BODY_PART_MAPPING).forEach(partId => {
        const part = document.getElementById(partId);
        if (part) {
            part.classList.add('body-part-transition');
            
            // Set initial color
            setPartColor(partId, COLORS.DEFAULT);
        }
    });
    
    console.log('✓ Body visualization initialized');
}

/**
 * Update body visualization based on detected and required PPE
 */
function updateBodyVisualization(detectedClasses, requiredClasses) {
    if (!svgLoaded) {
        console.warn('SVG not loaded yet');
        return;
    }
    
    currentDetected = detectedClasses || [];
    currentRequired = requiredClasses || [];
    
    // Convert to lowercase for case-insensitive comparison
    const detectedLower = currentDetected.map(c => c.toLowerCase());
    const requiredLower = currentRequired.map(c => c.toLowerCase());
    
    // Update each body part
    Object.keys(BODY_PART_MAPPING).forEach(partId => {
        const partClasses = BODY_PART_MAPPING[partId];
        const partClassesLower = partClasses.map(c => c.toLowerCase());
        
        // Check if this part is required
        const isRequired = partClassesLower.some(cls => 
            requiredLower.includes(cls)
        );
        
        // Check if this part is detected
        const isDetected = partClassesLower.some(cls => 
            detectedLower.includes(cls)
        );
        
        // Determine color
        let color;
        let shouldGlow = false;
        
        if (!isRequired) {
            color = COLORS.NOT_REQUIRED;
        } else if (isDetected) {
            color = COLORS.REQUIRED_DETECTED;
            shouldGlow = true;
        } else {
            color = COLORS.REQUIRED_MISSING;
            shouldGlow = true;
        }
        
        // Update part color
        setPartColor(partId, color);
        
        // Add glow animation
        const part = document.getElementById(partId);
        if (part) {
            part.classList.remove('glow-green', 'glow-red');
            
            if (shouldGlow) {
                if (isDetected) {
                    part.classList.add('glow-green');
                } else {
                    part.classList.add('glow-red');
                }
            }
        }
    });
}

/**
 * Set color for a body part
 */
function setPartColor(partId, color) {
    const part = document.getElementById(partId);
    if (!part) {
        console.warn(`Part ${partId} not found`);
        return;
    }
    
    // Update all fillable elements within the part
    const fillableElements = part.querySelectorAll('ellipse, circle, path, rect');
    fillableElements.forEach(element => {
        element.setAttribute('fill', color);
    });
    
    // Update stroke elements
    const strokeElements = part.querySelectorAll('line, path');
    strokeElements.forEach(element => {
        if (element.hasAttribute('stroke') && !element.hasAttribute('fill')) {
            element.setAttribute('stroke', color);
        }
    });
}

/**
 * Highlight missing PPE parts
 */
function highlightMissingPPE() {
    const detectedLower = currentDetected.map(c => c.toLowerCase());
    const requiredLower = currentRequired.map(c => c.toLowerCase());
    
    Object.keys(BODY_PART_MAPPING).forEach(partId => {
        const partClasses = BODY_PART_MAPPING[partId];
        const partClassesLower = partClasses.map(c => c.toLowerCase());
        
        const isRequired = partClassesLower.some(cls => requiredLower.includes(cls));
        const isDetected = partClassesLower.some(cls => detectedLower.includes(cls));
        
        if (isRequired && !isDetected) {
            // Flash the missing part
            const part = document.getElementById(partId);
            if (part) {
                part.classList.add('attention-animation');
                setTimeout(() => {
                    part.classList.remove('attention-animation');
                }, 1000);
            }
        }
    });
}

/**
 * Get status summary
 */
function getStatusSummary() {
    const detectedLower = currentDetected.map(c => c.toLowerCase());
    const requiredLower = currentRequired.map(c => c.toLowerCase());
    
    const missing = requiredLower.filter(cls => !detectedLower.includes(cls));
    const detected = requiredLower.filter(cls => detectedLower.includes(cls));
    
    return {
        total: requiredLower.length,
        detected: detected.length,
        missing: missing.length,
        missingList: missing,
        allDetected: missing.length === 0
    };
}

/**
 * Reset visualization
 */
function resetVisualization() {
    Object.keys(BODY_PART_MAPPING).forEach(partId => {
        setPartColor(partId, COLORS.DEFAULT);
        
        const part = document.getElementById(partId);
        if (part) {
            part.classList.remove('glow-green', 'glow-red', 'attention-animation');
        }
    });
}

// Export functions for use in other scripts
window.initBodyVisualization = initBodyVisualization;
window.updateBodyVisualization = updateBodyVisualization;
window.highlightMissingPPE = highlightMissingPPE;
window.getStatusSummary = getStatusSummary;
window.resetVisualization = resetVisualization;

console.log('Body visualization module loaded');



