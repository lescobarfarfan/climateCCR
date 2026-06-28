""" Class that implements a correlation matrix 

Including an algorithm to find the closest matrix that is positive semidefinite
"""

import numpy as np
import pandas as pd


class CorrelationMatrix:
    def __init__(self, file_path=None, epsilon=1e-5, correlation_matrix=None, underlyings=None) -> None:
        self.epsilon = epsilon

        if file_path is not None:
            self.correlation_matrix = pd.read_csv(file_path, index_col=0)
            self.underlyings = dict(
                zip(self.correlation_matrix.index.to_list(), range(len(self.correlation_matrix))))
            self.correlation_matrix = self.correlation_matrix.to_numpy()
        elif correlation_matrix is not None and underlyings is not None:
            self.correlation_matrix = correlation_matrix
            if len(underlyings) != len(self.correlation_matrix):
                raise ValueError(
                    f'Unequal number of underlyings and matrix indices.')
            self.underlyings = dict(
                zip(underlyings, range(len(self.correlation_matrix))))
        else:
            raise ValueError(
                f'Not sufficient data to construct correlation matrix.')

        # Check symmetry. If not likely bug in the block correlations file
        if (self.correlation_matrix != self.correlation_matrix.T).any():
            raise ValueError('The raw correlation matrix is not symmetric.')

        # Enforce positive-semidefined with Rebonato-Jaeckel rule
        # len([*filter(lambda x: x >= 0, eigen_values)]) != len(eigen_values)
        eigen_values, _ = np.linalg.eig(self.correlation_matrix)
        if np.any(eigen_values < 0):
            self.find_nearest_psd_matrix()

    # Based on Rebonato-Jaeckal:
    # https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1969689
    # https://stackoverflow.com/questions/10939213/how-can-i-calculate-the-nearest-positive-semi-definite-matrix
    # SEE DOMPAZ solution
    def find_nearest_psd_matrix(self):
        n = self.correlation_matrix.shape[0]
        eigval, eigvec = np.linalg.eig(self.correlation_matrix)
        val = np.matrix(np.maximum(eigval, self.epsilon))
        vec = np.matrix(eigvec)
        T = 1 / (np.multiply(vec, vec) * val.T)
        T = np.matrix(np.sqrt(np.diag(np.array(T).reshape((n)))))
        B = T * vec * np.diag(np.array(np.sqrt(val)).reshape((n)))
        self.correlation_matrix = B * B.T

    def get_correlation_matrix(self):
        return self.correlation_matrix

    def get_value(self, underlying1, underlying2):
        return self.correlation_matrix[self.underlyings[underlying1], self.underlyings[underlying2]]

    def get_cholesky_correlation_matrix(self):
        return np.linalg.cholesky(self.correlation_matrix)

    def get_underlying(self, index=None):
        if index is None:
            return self.underlyings
        else:
            return self.underlyings[index]

    def get_sub_correlation_matrix(self, underlyings):
        indices = []
        for u in underlyings:
            if u not in self.underlyings:
                raise ValueError(
                    f'No underlying {u} is found in the correlation matrix.')
            indices.append(self.underlyings[u])

        indices = np.asarray(indices)
        return CorrelationMatrix(correlation_matrix=self.correlation_matrix[indices, :][:, indices], underlyings=underlyings)
