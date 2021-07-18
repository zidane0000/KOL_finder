from datetime import datetime
import time


def write_to_log(verbose, text):
    if verbose:
        print(text)

    # Write to log
    if verbose == 2:
        date = datetime.fromtimestamp(time.time()).strftime('%Y%m%d')
        path = '{}.txt'.format(date)
        with open(path, 'a') as f:
            f.write(text)
            f.write('\n')
