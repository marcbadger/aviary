import torch
import torch.nn.functional as F
import numpy as np

from utils.geometry import perspective_projection

def gmof(x, sigma):
    """
    Implementation of robust Geman-McClure function
    """
    x_squared =  x ** 2
    sigma_squared = sigma ** 2
    return (sigma_squared * x_squared) / (sigma_squared + x_squared)