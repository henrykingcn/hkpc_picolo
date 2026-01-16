/**
 * HKPC PPE Detection System
 * Main JavaScript file for common functionality
 */

// Utility function to format dates
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// Utility function to format confidence scores
function formatConfidence(confidence) {
    return (confidence * 100).toFixed(1) + '%';
}

// Error handling for video stream
document.addEventListener('DOMContentLoaded', function() {
    const videoStream = document.getElementById('video-stream');
    
    if (videoStream) {
        videoStream.onerror = function() {
            console.error('Error loading video stream');
            // Could display an error message to the user
        };
    }
});

// Console log for debugging
console.log('HKPC PPE Detection System initialized');



