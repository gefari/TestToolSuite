from threading import Lock

l_print_lock = Lock()


def safe_print(*a, **b):
    """Thread safe print function"""
    with l_print_lock:
        print(*a, **b)