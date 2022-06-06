class Singleton(type):
    """
    Metaclass to make a class a singleton.
    """

    __instances: dict[type, object] = {}

    def __call__(cls, *args, **kwargs):
        """
        When the class is called, resolve with existing instances
        before creating a new one such that only one ever exists.
        """
        if cls not in cls.__instances:
            cls.__instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.__instances[cls]
