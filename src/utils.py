from time import time


def timer(f):
    '''
    A decorator to print the execution time of a method.
    Usage:
        @timer
        def some_function_to_profile(x, y, z):
    '''
    def t(*args, **kwargs):
        start_time = time()
        output = f(*args, **kwargs)
        end_time = time()
        delta_t = end_time - start_time
        print("\nExec time for '{}': {:.3f}s".format(f.__name__, delta_t))
        return output
    return t