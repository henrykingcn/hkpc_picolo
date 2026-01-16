/**
 * PIN Keypad Handler
 */

let pinValue = '';
const MAX_PIN_LENGTH = 6;

function updateDisplay() {
    for (let i = 1; i <= MAX_PIN_LENGTH; i++) {
        const dot = document.getElementById(`dot-${i}`);
        if (i <= pinValue.length) {
            dot.classList.add('filled');
        } else {
            dot.classList.remove('filled');
        }
    }
}

function addDigit(digit) {
    if (pinValue.length < MAX_PIN_LENGTH) {
        pinValue += digit;
        updateDisplay();
        
        // Auto-submit if PIN reaches minimum length (4) and user keeps typing
        if (pinValue.length === MAX_PIN_LENGTH) {
            setTimeout(submitPIN, 300);
        }
    }
}

function deleteDigit() {
    if (pinValue.length > 0) {
        pinValue = pinValue.slice(0, -1);
        updateDisplay();
    }
}

function submitPIN() {
    if (pinValue.length < 4) {
        showAlert('PIN must be at least 4 digits', 'error');
        return;
    }
    
    // Disable keypad during verification
    disableKeypad(true);
    
    // Send PIN to server
    fetch('/api/auth/pin', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ pin: pinValue })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Authentication successful!', 'success');
            // Store session token if provided
            if (data.token) {
                sessionStorage.setItem('admin_token', data.token);
            }
            // Redirect to admin dashboard
            setTimeout(() => {
                window.location.href = '/admin';
            }, 500);
        } else {
            showAlert(data.message, 'error');
            shakeDisplay();
            pinValue = '';
            updateDisplay();
            disableKeypad(false);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Connection error. Please try again.', 'error');
        pinValue = '';
        updateDisplay();
        disableKeypad(false);
    });
}

function showAlert(message, type) {
    const alertContainer = document.getElementById('alert-container');
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    alertContainer.innerHTML = '';
    alertContainer.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function shakeDisplay() {
    const display = document.getElementById('pin-display');
    display.classList.add('shake');
    setTimeout(() => {
        display.classList.remove('shake');
    }, 300);
}

function disableKeypad(disabled) {
    const keys = document.querySelectorAll('.key');
    keys.forEach(key => {
        key.disabled = disabled;
    });
}

// Keyboard support
document.addEventListener('keydown', (e) => {
    if (e.key >= '0' && e.key <= '9') {
        addDigit(e.key);
    } else if (e.key === 'Backspace') {
        e.preventDefault();
        deleteDigit();
    } else if (e.key === 'Enter') {
        e.preventDefault();
        submitPIN();
    }
});

// Check lock status on load
fetch('/api/auth/lock-status')
    .then(response => response.json())
    .then(data => {
        if (data.locked) {
            showAlert(`Account locked. Try again in ${data.remaining_time} seconds`, 'error');
            disableKeypad(true);
            
            // Re-enable after lockout period
            setTimeout(() => {
                location.reload();
            }, data.remaining_time * 1000);
        }
    })
    .catch(error => {
        console.error('Error checking lock status:', error);
    });



