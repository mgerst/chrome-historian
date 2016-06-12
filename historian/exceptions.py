class DoesNotExist(Exception):
    def __init__(self, type, index):
        super(DoesNotExist, self).__init__("{} with index {} does not exist".format(
            type.__name__, index
        ))