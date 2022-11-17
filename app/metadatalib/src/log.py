import os
from datetime import datetime

class Logger:
    def __init__(self, log_fp, err_fp = None):
        self.log_fp: str = log_fp
        self.err_fp: str = err_fp if err_fp else log_fp
        if not os.path.exists(os.path.dirname(self.log_fp)):
            try:
                os.makedirs(os.path.dirname(self.log_fp))
            except FileExistsError as e:
                None
        
        if not os.path.exists(os.path.dirname(self.err_fp)):
            try:
                os.makedirs(os.path.dirname(self.err_fp))
            except FileExistsError as e:
                None

    def log(self: object, msg: str):
        with open(self.log_fp, "a") as f:
            f.write(f"LOG: {datetime.now()} {msg}")
    
    def err(self: object, msg: str):
        with open(self.err_fp, "a") as f:
            f.write(f"ERR: {datetime.now()} {msg}")
