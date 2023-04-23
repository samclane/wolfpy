import math


class Vector2D:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        if isinstance(other, Vector2D):
            return self.x * other.x + self.y * other.y
        else:
            return Vector2D(self.x * other, self.y * other)

    def dot(self, other):
        return self.x * other.x + self.y * other.y

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalize(self):
        length = self.length()
        self.x /= length
        self.y /= length

    def sign(self, other):
        return self.x * other.y - self.y * other.x

    def min(self, other):
        return Vector2D(min(self.x, other.x), min(self.y, other.y))

    def max(self, other):
        return Vector2D(max(self.x, other.x), max(self.y, other.y))


class Hit:
    def __init__(self, val: int, side: int, pos: Vector2D):
        self.val = val
        self.side = side
        self.pos = pos
