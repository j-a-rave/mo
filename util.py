from math import sqrt


def lerp(a, b, r):
    return float(a) + ((float(b) - float(a)) * r)


def lerp_array(a, b, r):
    return [lerp(a[x], b[x], r) for x in range(len(a))]


def int_array(float_array):
    return [int(x) for x in float_array]


def midpoint_pos(a, b):
    return [(a[x] + b[x]) / 2 for x in range(len(a))]


def dist_sq_pos(a, b):
    components = [(b[x] - a[x]) for x in range(len(a))]
    val = 0
    for component in components:
        val = val + (component * component)
    return val


def capture_size(side_a, side_b, size):
    return sqrt(float(dist_sq_pos(side_a, side_b))) / float(size)


def capture_distance_pos(side_a, side_b, size):
    # given two positions within a total size, returns (-1, 1) scale position approximate
    return capture_size(side_a, side_b, size) * 2.0 - 1.0


def capture_pos(pos, size):
    # given x and width or y and height, returns (-1, 1) position
    return float(pos) / float(size) * 2.0 - 1.0


def translate_pos(pos, vec):
    return [pos[x] + vec[x] for x in range(len(pos))]


def vector_a_b(a, b, scalar=1.0):
    return [scalar * (b[x] - a[x]) for x in range(len(a))]
