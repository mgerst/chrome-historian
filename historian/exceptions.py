"""
Common exceptions used by chrome historian.
"""

class DoesNotExist(Exception):
    """
    Indicates that a query did not return results.
    """
    def __init__(self, type, index):
        """
        :param type: The type of thing being queried
        :param index: An id of the thing being queried
        """
        super(DoesNotExist, self).__init__("{} with index {} does not exist".format(
            type.__name__, index
        ))