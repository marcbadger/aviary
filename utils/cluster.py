import signal

class ClusterStateManager:
    """Handles job interruption signals on the cluster.

    ClusterStateManager can be used to decide when to
    save and exit from a task running on the cluster.

    
    Args:
        time_to_run: the time limit for your job
            CSM will return True for should_exit
            after this time

    """
    def __init__(self, time_to_run=7200):
        self.external_exit = None
        self.timer_exit = False

        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGALRM, self.timer_handler)
        signal.alarm(time_to_run)

    def signal_handler(self, signal, frame):
        print("Received signal [", signal, "]")
        self.external_exit = signal

    def timer_handler(self, signal, frame):
        print("Received alarm [", signal, "]")
        self.timer_exit = True

    def should_exit(self):
        if self.timer_exit:
            return True

        if self.external_exit is not None:
            return True

        return False

    def get_exit_code(self):
        if self.timer_exit:
            return 3

        if self.external_exit is not None:
            return 0

        return 0