from datetime import datetime

class Logger:
    def __init__(self, log_fp, err_fp: None) -> None:
        self.log_fp: str = log_fp
        self.err_fp: str = err_fp if err_fp else log_fp

    def log(self: object, msg: str):
        with open(self.log_fp, "a+") as f:
            f.write(f"LOG: {datetime.now()} {msg}")
    
    def err(self: object, msg: str):
        with open(self.err_fp, "a+") as f:
            f.write(f"ERR: {datetime.now()} {msg}")
