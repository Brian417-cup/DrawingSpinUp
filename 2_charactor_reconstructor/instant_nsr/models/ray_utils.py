import torch
import numpy as np


def get_ray_directions(W, H, fx, fy, cx, cy, use_pixel_centers=True):
    pixel_center = 0.5 if use_pixel_centers else 0
    i, j = np.meshgrid(
        np.arange(W, dtype=np.float32) + pixel_center,
        np.arange(H, dtype=np.float32) + pixel_center,
        indexing='xy'
    )
    i, j = torch.from_numpy(i), torch.from_numpy(j)

    # opencv system
    directions = torch.stack([(i - cx) / fx, (j - cy) / fy, torch.ones_like(i)], -1) # (H, W, 3)

    return directions


def get_ortho_ray_directions_origins(W, H, use_pixel_centers=True):
    pixel_center = 0.5 if use_pixel_centers else 0
    i, j = np.meshgrid(
        np.arange(W, dtype=np.float32) + pixel_center,
        np.arange(H, dtype=np.float32) + pixel_center,
        indexing='xy'
    )
    i, j = torch.from_numpy(i), torch.from_numpy(j)

    origins = torch.stack([(i/W-0.5)*2, (j/H-0.5)*2, torch.zeros_like(i)], dim=-1) # W, H, 3
    directions = torch.stack([torch.zeros_like(i), torch.zeros_like(j), torch.ones_like(i)], dim=-1) # W, H, 3

    return origins, directions


def get_ortho_rays(origins, directions, c2w, keepdim=False):
    # Rotate ray directions from camera coordinate to the world coordinate
    assert directions.shape[-1] == 3
    assert origins.shape[-1] == 3

    if directions.ndim == 2: # (N_rays, 3)
        assert c2w.ndim == 3 # (N_rays, 4, 4) / (1, 4, 4)
        rays_d = torch.matmul(c2w[:, :3, :3], directions[:, :, None]).squeeze()  # (N_rays, 3)
        rays_o = torch.matmul(c2w[:, :3, :3], origins[:, :, None]).squeeze()  # (N_rays, 3)
        rays_o = c2w[:,:3,3].expand(rays_d.shape) + rays_o  
    elif directions.ndim == 3: # (H, W, 3)
        if c2w.ndim == 2: # (4, 4)
            rays_d = torch.matmul(c2w[None, None, :3, :3], directions[:, :, :, None]).squeeze()  # (H, W, 3)
            rays_o = torch.matmul(c2w[None, None, :3, :3], origins[:, :, :, None]).squeeze()  # (H, W, 3)
            rays_o = c2w[None, None,:3,3].expand(rays_d.shape) + rays_o  
        elif c2w.ndim == 3: # (B, 4, 4)
            rays_d = torch.matmul(c2w[:,None, None, :3, :3], directions[None, :, :, :, None]).squeeze()  # # (B, H, W, 3)
            rays_o = torch.matmul(c2w[:,None, None, :3, :3], origins[None, :, :, :, None]).squeeze()  # # (B, H, W, 3)
            rays_o = c2w[:,None, None, :3,3].expand(rays_d.shape) + rays_o  

    if not keepdim:
        rays_o, rays_d = rays_o.reshape(-1, 3), rays_d.reshape(-1, 3)

    return rays_o, rays_d
