# from enum import Enum
import pygame.gfxdraw
import math

class NordColors:
    nord0 = (46,52,64)
    nord1 = (59,66,82)
    nord2 = (67,76,94)
    nord3 = (76,86,106)
    snow0 = (216,222,233)
    snow1 = (229,233,240)
    snow2 = (236,239,244)
    frost0 = (143,188,187)
    frost1 = (136,192,208)
    frost2 = (129,161,193)
    frost3 = (94,129,172)
    aurora0 = (191,97,106)
    aurora1 = (208,135,112)
    aurora2 = (235,203,139)
    aurora3 = (163,190,140)
    aurora4 = (180,142,173)

def fill_arc(surf, center, radius, theta0, theta1, color, ndiv=50):
    x0, y0 = center
    dtheta = (theta1-theta0)/ndiv
    angles = [theta0+i*dtheta for i in range(ndiv+1)]
    points = [(x0,y0)] + [(x0+radius*math.cos(theta),y0-radius*math.sin(theta)) for theta in angles]
    # pygame.draw.polygon(surf, color, points)
    pygame.gfxdraw.filled_polygon(surf, points, color)