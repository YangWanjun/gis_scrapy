import scrapy
import zipfile
import csv
from io import BytesIO
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
            desc=desc if desc else name,
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

    def download_zip(self, response):
        return zipfile.ZipFile(BytesIO(response.body))

    def read_csv_from_text(self, text, has_header=False):
        line_count = len(text.strip().splitlines())
        reader = csv.reader(text.strip().splitlines())
        if has_header:
            header = next(reader)
        else:
            header = None
        for i, row in enumerate(reader):
            if header:
                data = dict(zip(header, row))
                yield i, line_count, data
            else:
                yield i, line_count, row
