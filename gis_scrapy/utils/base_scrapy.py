import scrapy
from tqdm import tqdm


class BaseSpider(scrapy.Spider):
    custom_settings = {
        'LOG_LEVEL': 'WARNING',
    }
    processes = {}

    def add_process(self, name, total, desc=None):
        self.processes[name] = tqdm(
            total=total,
            unit='it',
            desc=desc,
            ncols=70,
        )

    def update_process(self, name, step=1):
        process = self.processes.get(name)
        if process:
            process.update(step)

    def end_processes(self, name=None):
        if name:
            process = self.processes.get(name)
            process.close()
        elif self.processes:
            for name, process in self.processes.items():
                process.close()
