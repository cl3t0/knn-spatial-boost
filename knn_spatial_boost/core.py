# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_core.ipynb.

# %% auto 0
__all__ = ['Estimator', 'Columns', 'KNNSpatialBooster']

# %% ../nbs/00_core.ipynb 3
Estimator = t.Any
Columns = t.Union[t.Literal["*"], t.List[int]]


@dataclass
class KNNSpatialBooster:
    """
    A KNN Spatial Booster.

    You can use it with any model. It uses the training dataset to improve
    the spatial perception of the model adding more features.

    Read more in the `KNNSpatialBooster` docs.

    Parameters
    ----------

    n_neighbors : int, default=5
        The number of neighbors to use as feature.

    estimator : Estimator, default=RandomForestRegressor()
        Any Estimator as defined by scikit-learn.

    estimator_output_1d_array : bool, default=True
        Used to be compatible with estimators that needs 1d arrays in `.fit()`.

    spatial_features : Columns, default="*"
        Define which columns should be used as coordinates for KNN.
    
    remove_target_spatial_cols : bool, default=False
        Set to True if you believe the model should not use the original
        spatial features in the training process.
    
    remove_neighbor_spatial_cols : bool, default=True
        Set to True if you believe the model should not use the neighbors
        spatial features in the training process.
    """
    n_neighbors: int = field(default=5)
    estimator: Estimator = field(default=RandomForestRegressor())
    estimator_output_1d_array: bool = field(default=True)
    spatial_features: Columns = field(default="*")
    remove_target_spatial_cols: bool = field(default=False)
    remove_neighbor_spatial_cols: bool = field(default=True)
    
    def fit(self, X: np.ndarray, Y: np.ndarray) -> None:
        """
        Fit model for X and Y.

        Parameters
        ----------

        X : np.ndarray
            Shape must be (number of samples,) or (number of samples, number_of_features).
        Y : np.ndarray
            Shape must be (number of samples,) or (number of samples, number of outputs).

        """
        if len(X.shape) < 1 or len(X.shape) > 2:
            raise Exception(f"Bad X shape: {X.shape}")

        if len(Y.shape) < 1 or len(Y.shape) > 2:
            raise Exception(f"Bad Y shape: {Y.shape}")

        self.X = X if len(X.shape) == 2 else X.reshape((X.shape[0], 1))
        self.Y = Y if len(Y.shape) == 2 else Y.reshape((Y.shape[0], 1))

        self.spatial_cols = (
            list(range(self.X.shape[1]))
            if self.spatial_features == "*"
            else self.spatial_features
        )

        boosted_X = KNNSpatialBooster.knn_enrichment(
            self.X,
            self.Y,
            self.X,
            self.spatial_cols,
            self.n_neighbors,
            remove_first_neighbor=True,
            remove_target_spatial_cols=self.remove_target_spatial_cols,
            remove_neighbor_spatial_cols=self.remove_neighbor_spatial_cols,
        )
        self.estimator.fit(
            boosted_X, Y.ravel() if self.estimator_output_1d_array else Y
        )

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict for X.

        Parameters
        ----------

        X : np.ndarray
            Shape must be (number of samples,) or (number of samples, number_of_features).

        Returns
        -------

        Y : np.ndarray
            Predicted value for given X.
        """

        boosted_X = KNNSpatialBooster.knn_enrichment(
            self.X,
            self.Y,
            X,
            self.spatial_cols,
            self.n_neighbors,
            remove_target_spatial_cols=self.remove_target_spatial_cols,
            remove_neighbor_spatial_cols=self.remove_neighbor_spatial_cols,
        )
        return self.estimator.predict(boosted_X)

    def score(self, X: np.ndarray, Y: np.ndarray) -> float:
        """
        Calculate score for X and Y. It uses the estimator score function.

        Parameters
        ----------

        X : np.ndarray
            Shape must be (number of samples,) or (number of samples, number_of_features).
        Y : np.ndarray
            Shape must be (number of samples,) or (number of samples, number of outputs).

        Returns
        -------

        score : float
            Estimator score.
        """

        boosted_X = KNNSpatialBooster.knn_enrichment(
            self.X,
            self.Y,
            X,
            self.spatial_cols,
            self.n_neighbors,
            remove_target_spatial_cols=self.remove_target_spatial_cols,
            remove_neighbor_spatial_cols=self.remove_neighbor_spatial_cols,
        )
        return self.estimator.score(boosted_X, Y)

    @staticmethod
    def knn_enrichment(
        base_X: np.ndarray,
        base_y: np.ndarray,
        target_X: np.ndarray,
        spatial_cols: t.List[int],
        n_neighbors: int,
        remove_first_neighbor: bool = False,
        remove_target_spatial_cols: bool = False,
        remove_neighbor_spatial_cols: bool = True,
    ) -> np.ndarray:
        first_index = 1 if remove_first_neighbor else 0
        k = n_neighbors + first_index
        btree = cKDTree(base_X[:, spatial_cols])
        distances, indexes = btree.query(target_X[:, spatial_cols], k=k)

        neighbors_cols = [
            i
            for i in range(base_X.shape[1])
            if not (remove_neighbor_spatial_cols and (i in spatial_cols))
        ]

        neighbors_tuples = [
            (
                base_X[idx.ravel(), :][:, neighbors_cols],
                np.reciprocal(d + 1),
                base_y[idx.ravel(), :],
            )
            for d, idx in zip(np.hsplit(distances, k), np.hsplit(indexes, k))
        ]

        neighbors = [np.hstack(neighbors_tuple) for neighbors_tuple in neighbors_tuples]

        taget_cols = [
            i
            for i in range(target_X.shape[1])
            if not (remove_target_spatial_cols and (i in spatial_cols))
        ]

        return np.hstack([target_X[:, taget_cols], *neighbors[first_index:]])

