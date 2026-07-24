---
name: Torch sparse degree computation
description: Use scatter_add_ on crow/col indices, never .to_dense() or torch.sparse.sum on CSR
type: feedback
originSessionId: 41cb975b-2fcc-4d41-be27-99570b4f02ce
---
Computing row/column sums on `torch.sparse_csr_tensor` requires the scatter_add_ pattern — NOT `.to_dense()` or `torch.sparse.sum()`.

**Why:** `.to_dense()` allocates O(N²) memory (OOM on production graphs); `torch.sparse.sum()` raises `NotImplementedError` on CPU for CSR tensors. Both fail silently in tests (small matrices) but explode in production.

**How to apply:** When implementing any degree-based normalization with torch sparse CSR:
```python
crow = A.crow_indices()
col = A.col_indices()
val = A.values().float()
row_lengths = torch.diff(crow).to(dtype=torch.int64)
rows = torch.repeat_interleave(torch.arange(N, device=device, dtype=torch.int64), row_lengths)
d_out = torch.zeros(N, dtype=torch.float32, device=device)
d_out.scatter_add_(0, rows, val)
d_in = torch.zeros(N, dtype=torch.float32, device=device)
d_in.scatter_add_(0, col, val)
```
This is O(nnz) memory and works on both CPU and CUDA.
