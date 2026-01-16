"""
Body Parts Mapping Configuration
Maps PPE detection classes to SVG body parts for visualization
"""

# Mapping of SVG body part IDs to PPE detection classes
BODY_PART_MAPPING = {
    'head': {
        'classes': ['Head', 'Helmet'],
        'display_name': 'Head/Helmet',
        'priority': 1
    },
    'face': {
        'classes': ['Face', 'Face-mask-medical'],
        'display_name': 'Face/Mask',
        'priority': 2
    },
    'eyes': {
        'classes': ['Glasses', 'Face-guard'],
        'display_name': 'Eye Protection',
        'priority': 3
    },
    'ears': {
        'classes': ['Ear', 'Earmuffs'],
        'display_name': 'Ear Protection',
        'priority': 5
    },
    'mouth': {
        'classes': ['Face-mask-medical'],
        'display_name': 'Face Mask',
        'priority': 4
    },
    'chest': {
        'classes': ['Safety-vest', 'Medical-suit', 'Safety-suit'],
        'display_name': 'Body Protection',
        'priority': 6
    },
    'hands-left': {
        'classes': ['Hands', 'Gloves'],
        'display_name': 'Left Hand/Glove',
        'priority': 7
    },
    'hands-right': {
        'classes': ['Hands', 'Gloves'],
        'display_name': 'Right Hand/Glove',
        'priority': 8
    },
    'feet': {
        'classes': ['Foot', 'Shoes'],
        'display_name': 'Footwear',
        'priority': 9
    }
}

# Color codes for different states
BODY_PART_COLORS = {
    'required_detected': '#10B981',      # Green - Required and detected
    'required_missing': '#EF4444',       # Red - Required but missing
    'not_required': '#9CA3AF',           # Gray - Not required
    'checking': '#F59E0B',               # Yellow - Checking/uncertain
    'default': '#D1D5DB'                 # Light gray - Default
}


def get_body_part_status(detected_classes, required_classes):
    """
    Determine the status and color for each body part
    
    Args:
        detected_classes: List of detected PPE classes (lowercase)
        required_classes: List of required PPE classes (from config)
        
    Returns:
        dict: Mapping of body part ID to status info
    """
    status = {}
    
    # Convert to lowercase for case-insensitive comparison
    detected_lower = [cls.lower() for cls in detected_classes]
    required_lower = [cls.lower() for cls in required_classes]
    
    for part_id, part_info in BODY_PART_MAPPING.items():
        part_classes = part_info['classes']
        part_classes_lower = [cls.lower() for cls in part_classes]
        
        # Check if this part is required
        is_required = any(cls.lower() in required_lower for cls in part_classes)
        
        # Check if this part is detected
        is_detected = any(cls.lower() in detected_lower for cls in part_classes)
        
        # Determine color and status
        if not is_required:
            color = BODY_PART_COLORS['not_required']
            state = 'not_required'
        elif is_detected:
            color = BODY_PART_COLORS['required_detected']
            state = 'detected'
        else:
            color = BODY_PART_COLORS['required_missing']
            state = 'missing'
        
        status[part_id] = {
            'color': color,
            'state': state,
            'required': is_required,
            'detected': is_detected,
            'display_name': part_info['display_name']
        }
    
    return status


def get_missing_ppe(detected_classes, required_classes):
    """
    Get list of missing PPE items
    
    Args:
        detected_classes: List of detected PPE classes
        required_classes: List of required PPE classes
        
    Returns:
        list: Names of missing PPE items
    """
    detected_lower = [cls.lower() for cls in detected_classes]
    missing = []
    
    for req_class in required_classes:
        if req_class.lower() not in detected_lower:
            missing.append(req_class)
    
    return missing


if __name__ == "__main__":
    # Test the mapping
    detected = ['head', 'hands', 'glasses']
    required = ['Head', 'Hands', 'Glasses', 'Helmet']
    
    status = get_body_part_status(detected, required)
    for part_id, info in status.items():
        print(f"{part_id}: {info['state']} - {info['color']}")
    
    missing = get_missing_ppe(detected, required)
    print(f"\nMissing PPE: {missing}")



