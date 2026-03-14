import json
import logging

class JsonLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log(self, message, **kwargs):
        log_entry = {'message': message, 'data': kwargs}
        self.logger.info(json.dumps(log_entry))

# Example usage:
# json_logger = JsonLogger('my_logger')
# json_logger.log('This is a log message', context='example', success=True)