def gaussian_smooth(adjacency: list[list[int]], scalar: np.ndarray, mask: np.ndarray | None, strength: float, passes: int) -> np.ndarray:
    n = len(adjacency)
    smoothed_array: np.ndarray = np.zeros(n, dtype=np.float64)
    
    for i in range(n):

