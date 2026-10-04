"""Class that implements a correlation matrix

Including an algorithm to find the closest matrix that is positive semidefinite
"""

import numpy as np
import pandas as pd


class CorrelationMatrix:
    def __init__(
        self, file_path=None, epsilon=1e-5, correlation_matrix=None, underlyings=None
    ) -> None:
        self.epsilon = epsilon

        if file_path is not None:
            self.correlation_matrix = pd.read_csv(file_path, index_col=0)
            self.underlyings = dict(
                zip(
                    self.correlation_matrix.index.to_list(),
                    range(len(self.correlation_matrix)),
                    strict=False,
                )
            )
            self.correlation_matrix = self.correlation_matrix.to_numpy()
        elif correlation_matrix is not None and underlyings is not None:
            self.correlation_matrix = correlation_matrix
            if len(underlyings) != len(self.correlation_matrix):
                raise ValueError("Unequal number of underlyings and matrix indices.")
            self.underlyings = dict(
                zip(underlyings, range(len(self.correlation_matrix)), strict=False)
            )
        else:
            raise ValueError("Not sufficient data to construct correlation matrix.")

        # Check symmetry. If not likely bug in the block correlations file
        if (self.correlation_matrix != self.correlation_matrix.T).any():
            raise ValueError("The raw correlation matrix is not symmetric.")

        # Enforce positive-semidefiniteness with the Rebonato-Jaeckel rule. The
        # matrix is symmetric (checked above), so the symmetric eigensolver is the
        # right tool: real, sorted eigenvalues, no ndarray/matrix mixing (CCR-SIM-02).
        self.correlation_matrix = np.asarray(self.correlation_matrix, dtype=float)
        if np.any(np.linalg.eigvalsh(self.correlation_matrix) < 0):
            self.find_nearest_psd_matrix()

    # Based on Rebonato-Jaeckel:
    # https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1969689
    # https://stackoverflow.com/questions/10939213/how-can-i-calculate-the-nearest-positive-semi-definite-matrix
    # SEE DOMPAZ solution
    def find_nearest_psd_matrix(self):
        """Replace the matrix by its nearest unit-diagonal PSD matrix (Rebonato-Jaeckel).

        Eigenvalues are floored at ``epsilon``; the reconstruction ``B @ B.T`` is
        invariant to the eigenvector sign/order conventions of the LAPACK build, so
        only ulp-level differences can arise across BLAS implementations. The result
        is symmetrised explicitly because the constructor's exact-symmetry check runs
        on every sub-matrix and a blocked GEMM is not guaranteed to return bit-equal
        (i, j) and (j, i) entries on every platform.
        """
        eigval, eigvec = np.linalg.eigh(self.correlation_matrix)
        val = np.maximum(eigval, self.epsilon)
        scale = 1.0 / ((eigvec * eigvec) @ val)  # T_i = 1 / sum_k v_ik^2 lambda_k
        B = (np.sqrt(scale)[:, None] * eigvec) * np.sqrt(val)[None, :]
        nearest = B @ B.T
        self.correlation_matrix = 0.5 * (nearest + nearest.T)

    def get_correlation_matrix(self):
        return self.correlation_matrix

    def get_value(self, underlying1, underlying2):
        return self.correlation_matrix[self.underlyings[underlying1], self.underlyings[underlying2]]

    def get_sub_correlation_matrix(self, underlyings):
        indices = []
        for u in underlyings:
            if u not in self.underlyings:
                raise ValueError(f"No underlying {u} is found in the correlation matrix.")
            indices.append(self.underlyings[u])

        indices = np.asarray(indices)
        return CorrelationMatrix(
            correlation_matrix=self.correlation_matrix[indices, :][:, indices],
            underlyings=underlyings,
        )
