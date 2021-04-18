"""Base class for task generator. A task generator is an iterable, it gets 
    input from configs, and in every iteration, it output the task command and
    the log file name to save. For detailed example, please refer to 
    `SleepGenerator.py`.
"""
class TaskGeneratorBase:
    """customized configs in config.yml will passed by kwargs. Please keep 
        `**kwargs` exist to collect unused arguments.
    """
    def __init__(self, **kwargs):
        pass

    """after initialization, the class should be available to response the
        total number of tasks
    """
    def __len__(self):
        raise NotImplementedError

    """get next command.
        Args:
            prefix: command prefix, without device and number information
            IP: target IP
            device: device type. For CPU is '-', for GPU is the GPU ID.
            threadnumber: thread number.
        Returns:
            If all commands are generated, raise StopIteration.
            otherwise, return a tuple containing two strings (X, Y).
            X: generated command based on input arguments.
            Y: logfile name.
    """
    def get_next_command(self, prefix, IP, device, threadnumber):
        raise NotImplementedError

