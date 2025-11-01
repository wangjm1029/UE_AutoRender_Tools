"""
Motion Pattern Calculation Module
==================================
Provides calculation functions for all 20+ motion patterns.
Each function returns (x, y, z) coordinates for the current frame.
"""

import math


def calculate_sine_wave(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Sine wave motion along X-axis with Y-axis oscillation"""
    current_x = sx + alpha * params['total_distance']
    t = alpha * params['y_frequency'] * 2 * math.pi
    if frame_index == num_frames - 1:
        t -= 1e-6
    current_y = sy + params['y_amplitude'] * math.sin(t)
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_z_shape(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Three-segment Z-shaped trajectory"""
    if alpha < 0.33:
        segment_alpha = alpha / 0.33
        current_x = sx + segment_alpha * params['total_distance'] * 0.4
        current_y = sy + segment_alpha * params['y_amplitude']
    elif alpha < 0.67:
        segment_alpha = (alpha - 0.33) / 0.34
        current_x = sx + (0.4 + segment_alpha * 0.4) * params['total_distance']
        current_y = sy + params['y_amplitude']
    else:
        segment_alpha = (alpha - 0.67) / 0.33
        current_x = sx + (0.8 + segment_alpha * 0.2) * params['total_distance']
        current_y = sy + params['y_amplitude'] * (1 - segment_alpha)
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_circle(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Circular motion while advancing along X-axis"""
    t = alpha * params['y_frequency'] * 2 * math.pi
    if frame_index == num_frames - 1:
        t -= 1e-6
    r = abs(params['y_amplitude'])
    center_x = sx + alpha * params['total_distance']
    current_x = center_x + r * math.cos(t)
    current_y = sy + r * math.sin(t)
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_spiral(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Spiral motion with expanding radius"""
    t = alpha * params['y_frequency'] * 2 * math.pi
    if frame_index == num_frames - 1:
        t -= 1e-6
    r = abs(params['y_amplitude']) * alpha
    center_x = sx + alpha * params['total_distance']
    current_x = center_x + r * math.cos(t)
    current_y = sy + r * math.sin(t)
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_square_wave(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Square wave pattern on Y-axis"""
    segment = int(alpha * 4)
    segment_alpha = (alpha * 4) % 1.0
    current_x = sx + alpha * params['total_distance']
    if segment % 2 == 0:
        current_y = sy + params['y_amplitude'] * segment_alpha
    else:
        current_y = sy + params['y_amplitude'] * (1 - segment_alpha)
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_zigzag(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Zigzag motion pattern"""
    segments = max(2, int(params['y_frequency'] * 4))
    pos = alpha * segments
    seg_index = int(pos)
    seg_alpha = pos - seg_index
    direction = 1 if seg_index % 2 == 0 else -1
    current_x = sx + alpha * params['total_distance']
    current_y = sy + direction * seg_alpha * params['y_amplitude']
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_triangle_wave(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Triangle wave pattern"""
    t = (alpha * params['y_frequency']) % 1.0
    if frame_index == num_frames - 1:
        t -= 1e-6
    tri = 1.0 - abs(2 * t - 1)
    current_x = sx + alpha * params['total_distance']
    current_y = sy + (tri * 2 - 1) * params['y_amplitude'] * 0.5
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_ellipse(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Elliptical motion pattern"""
    t = alpha * params['y_frequency'] * 2 * math.pi
    if frame_index == num_frames - 1:
        t -= 1e-6
    rx = abs(params['total_distance']) * 0.05
    ry = abs(params['y_amplitude'])
    current_x = sx + alpha * params['total_distance'] + rx * math.cos(t)
    current_y = sy + ry * 0.6 * math.sin(t)
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_figure8(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Figure-8 motion pattern"""
    t = alpha * params['y_frequency'] * 2 * math.pi
    if frame_index == num_frames - 1:
        t -= 1e-6
    a = params['y_amplitude'] * 0.5
    denom = 1 + math.sin(t) ** 2
    offset_x = a * math.sin(t) / denom
    offset_y = a * math.sin(t) * math.cos(t) / denom
    current_x = sx + alpha * params['total_distance'] + offset_x
    current_y = sy + offset_y
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_arc(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Arc motion pattern"""
    t = alpha * math.pi
    if frame_index == num_frames - 1:
        t -= 1e-6
    current_x = sx + alpha * params['total_distance']
    current_y = sy + params['y_amplitude'] * math.sin(t)
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_bounce(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Bouncing motion with decay"""
    t = alpha * params['y_frequency'] * math.pi
    if frame_index == num_frames - 1:
        t -= 1e-6
    decay = 1.0 - 0.3 * alpha
    current_x = sx + alpha * params['total_distance']
    current_y = sy + decay * params['y_amplitude'] * abs(math.sin(t))
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_sawtooth(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Sawtooth wave pattern"""
    t = (alpha * params['y_frequency']) % 1.0
    if frame_index == num_frames - 1:
        t -= 1e-6
    current_x = sx + alpha * params['total_distance']
    current_y = sy + (t * 2 - 1) * params['y_amplitude'] * 0.5
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_serpentine(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Serpentine wave pattern"""
    t = alpha * params['y_frequency'] * 2 * math.pi
    if frame_index == num_frames - 1:
        t -= 1e-6
    current_x = sx + alpha * params['total_distance']
    current_y = sy + params['y_amplitude'] * (math.sin(t) * 0.7 + math.sin(t * 0.5) * 0.3)
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_lissajous(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Lissajous curve pattern"""
    t = alpha * 2 * math.pi
    if frame_index == num_frames - 1:
        t -= 1e-6
    a = params['y_frequency']
    b = params['y_frequency'] * 1.5
    current_x = sx + alpha * params['total_distance'] + (params['y_amplitude'] * 0.3) * math.sin(a * t)
    current_y = sy + params['y_amplitude'] * math.sin(b * t + math.pi / 2)
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_pendulum(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Pendulum motion with envelope"""
    t = alpha * params['y_frequency'] * 2 * math.pi
    if frame_index == num_frames - 1:
        t -= 1e-6
    envelope = 1.0 - 0.5 * abs(2 * alpha - 1)
    current_x = sx + alpha * params['total_distance']
    current_y = sy + envelope * params['y_amplitude'] * math.sin(t)
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_expand_circle(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Circle with expanding/contracting radius"""
    t = alpha * params['y_frequency'] * 2 * math.pi
    if frame_index == num_frames - 1:
        t -= 1e-6
    r = params['y_amplitude'] * (0.5 + 0.5 * math.sin(alpha * math.pi))
    center_x = sx + alpha * params['total_distance']
    current_x = center_x + r * math.cos(t)
    current_y = sy + r * math.sin(t)
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_rectangle_loop(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Rectangular loop pattern"""
    loops = max(1, int(params['y_frequency']))
    p = (alpha * loops) % 1.0
    if frame_index == num_frames - 1:
        p -= 1e-6
    width = abs(params['total_distance']) * 0.1
    height = params['y_amplitude']
    base_x = sx + alpha * params['total_distance']
    if p < 0.25:
        k = p / 0.25
        current_x = base_x - width / 2
        current_y = sy + k * height
    elif p < 0.5:
        k = (p - 0.25) / 0.25
        current_x = base_x - width / 2 + k * width
        current_y = sy + height
    elif p < 0.75:
        k = (p - 0.5) / 0.25
        current_x = base_x + width / 2
        current_y = sy + height * (1 - k)
    else:
        k = (p - 0.75) / 0.25
        current_x = base_x + width / 2 - k * width
        current_y = sy
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_diamond(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Diamond-shaped pattern"""
    p = (alpha * params['y_frequency']) % 1.0
    if frame_index == num_frames - 1:
        p -= 1e-6
    height = params['y_amplitude']
    width = abs(params['total_distance']) * 0.08
    center_x = sx + alpha * params['total_distance']
    if p < 0.25:
        k = p / 0.25
        current_x = center_x
        current_y = sy + k * height
    elif p < 0.5:
        k = (p - 0.25) / 0.25
        current_x = center_x + k * width
        current_y = sy + height * (1 - k)
    elif p < 0.75:
        k = (p - 0.5) / 0.25
        current_x = center_x + width * (1 - k)
        current_y = sy - k * height
    else:
        k = (p - 0.75) / 0.25
        current_x = center_x - k * width
        current_y = sy - height * (1 - k)
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_infinity_horizontal(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Horizontal infinity (∞) pattern"""
    t = alpha * params['y_frequency'] * 2 * math.pi
    if frame_index == num_frames - 1:
        t -= 1e-6
    a = params['y_amplitude'] * 0.5
    current_x = sx + alpha * params['total_distance'] + a * math.sin(t)
    current_y = sy + a * math.sin(t) * math.cos(t)
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_random_walk(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Pseudo-random walk pattern"""
    t = alpha * params['y_frequency'] * 2 * math.pi
    if frame_index == num_frames - 1:
        t -= 1e-6
    jitter_x = (params['y_amplitude'] * 0.2) * (math.sin(7 * t) + math.sin(5.3 * t) * 0.5)
    jitter_y = (params['y_amplitude'] * 0.6) * (math.sin(3.1 * t) + 0.5 * math.sin(9 * t))
    current_x = sx + alpha * params['total_distance'] + jitter_x
    current_y = sy + max(-params['y_amplitude'], min(params['y_amplitude'], jitter_y))
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_static_rotation(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Static position with rotation only"""
    current_x = sx
    current_y = sy
    current_z = sz
    return (current_x, current_y, current_z)


def calculate_linear(alpha, sx, sy, sz, frame_index, num_frames, params):
    """Linear/straight-line motion (default)"""
    current_x = sx + alpha * params['total_distance']
    current_y = sy
    current_z = sz
    return (current_x, current_y, current_z)


# Motion pattern registry
MOTION_CALCULATORS = {
    "sine_wave": calculate_sine_wave,
    "z_shape": calculate_z_shape,
    "circle": calculate_circle,
    "spiral": calculate_spiral,
    "square_wave": calculate_square_wave,
    "zigzag": calculate_zigzag,
    "triangle_wave": calculate_triangle_wave,
    "ellipse": calculate_ellipse,
    "figure8": calculate_figure8,
    "arc": calculate_arc,
    "bounce": calculate_bounce,
    "sawtooth": calculate_sawtooth,
    "serpentine": calculate_serpentine,
    "lissajous": calculate_lissajous,
    "pendulum": calculate_pendulum,
    "expand_circle": calculate_expand_circle,
    "rectangle_loop": calculate_rectangle_loop,
    "diamond": calculate_diamond,
    "infinity_horizontal": calculate_infinity_horizontal,
    "random_walk": calculate_random_walk,
    "static_rotation": calculate_static_rotation,
    "linear": calculate_linear,
}


def get_position_for_motion(motion_type, alpha, start_x, start_y, start_z, 
                            frame_index, num_frames, motion_params):
    """
    Unified dispatcher for all motion patterns
    
    Args:
        motion_type: Name of the motion pattern
        alpha: Progress through animation (0.0 to 1.0)
        start_x, start_y, start_z: Initial position
        frame_index: Current frame index
        num_frames: Total number of frames
        motion_params: Dictionary with motion parameters (total_distance, y_amplitude, etc.)
    
    Returns:
        (x, y, z) tuple with calculated position
    """
    calculator = MOTION_CALCULATORS.get(motion_type, calculate_linear)
    return calculator(alpha, start_x, start_y, start_z, frame_index, num_frames, motion_params)
