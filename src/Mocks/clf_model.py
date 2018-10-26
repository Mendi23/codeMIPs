
from sklearn.base import BaseEstimator, ClassifierMixin
from src.MIP import Mip
from sklearn.model_selection import GridSearchCV

class MIP_model(BaseEstimator, ClassifierMixin):
    """
    Implementation of the MIP model (Mutual Influence Potential Networks),
    compatible with the sklearn API
    """

    def __init__(self, alpha=0.2, beta=0.6, gamma=0.2, userDecay=1.0, objectDecay=1.0):
        """
        @:param alpha, beta, gamma
        @:param user_decay, object_decay
        """
        self.alpha = alpha  # weight given to the global importance (centrality) of the object
        self.beta = beta  # weight given to the proximity between the user and the object
        self.gamma = gamma  # weight given to the extent of change
        self.userDecay = userDecay  # the decay for weights of edges between user and objects he didn't interact with in the session
        self.objectDecay = objectDecay  # the decay for weights of edges between 2 objects, when only one of them has changes in the sessin


    def fit(self, X, y):
        """
        :param X:
        :param y:
        """
        if X.shape[0] != y.shape[0]:
            raise ValueError #not sure why, but this requierment need to be met

        self.model_ = Mip(alpha=self.alpha,
                        beta=self.beta,
                        gamma=self.gamma,
                        user_decay=self.userDecay,
                        object_decay=self.objectDecay)
        return self


