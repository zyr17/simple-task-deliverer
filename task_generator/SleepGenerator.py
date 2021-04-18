from .TaskGeneratorBase import TaskGeneratorBase

class SleepGenerator(TaskGeneratorBase):
    def __init__(self, sleep_time = '10s', sleep_task_count = 10, **kwargs):
        self.sleep = sleep_time
        if isinstance(self.sleep, int):
            self.sleep = str(self.sleep) + 's'
        self.count = sleep_task_count
        self.now = 0

    def __len__(self):
        return self.count

    def get_next_command(self, prefix, IP, device, threadnumber):
        if self.count == self.now:
            raise StopIteration
        self.now += 1
        return (
            "sleep %s; echo sleep over." % self.sleep,
            "sleep_%03d_%s_%s_%s" % (self.now, str(IP), str(device), 
                                     str(threadnumber))
        )
