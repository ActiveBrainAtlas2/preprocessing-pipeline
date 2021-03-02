from threading import Thread
from multiprocessing import Process
from os import remove
import argparse

from time import time

class IOTest:
    max_workers = 10
    max_lines = 10000000    
    file_location = '/home/eddyod/tmp/db'
    
    worker_model = None
    
    def __init__(self, max_attempts):
        self.name = self.__class__.__name__
        self.max_attempts = max_attempts
    
    def write(self, pid):
        p = self.__class__.__name__ + str(pid)
        filename = '%s/%s.txt' % (self.file_location, p)
        with open(filename, 'w') as f:
            for x in range(self.max_lines):
                f.write('Nothing signed "THE MGT." would ever be challenged; the Midget could always pass himself off as the Management.\n')
        remove(filename)
                
    def run(self):
        results = []
        print('Starting', self.name, '...')
        for attempt in range(self.max_attempts):
            # Create N workers
            workers = []
            for y in range(self.max_workers):
                workers.append(self.worker_model(target=self.write, args=(y,)))
                
            start_time = time()
            [t.start() for t in workers]
            [t.join() for t in workers]
            elapsed = time() - start_time
            results.append(elapsed)
            print('%s attempt %i of %i took %s seconds to write %i lines to %i files.' % (self.name, attempt+1, self.max_attempts, elapsed, self.max_lines, self.max_workers))
            
        print('-' * 80)
        print(self.name, 'results:', [round(x,2) for x in results])
        print('avg:', sum(results) / len(results))
        print('-' * 80)
        
        return sum(results) / len(results)
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--tests', help='Enter the # of tests', required=False, default=2)
    args = parser.parse_args()
    tests = int(args.tests)



    class Multithreaded(IOTest):
        worker_model = Thread
        
    class Multiprocessed(IOTest):
        worker_model = Process
        
    thread_avg = Multithreaded(tests).run()
    process_avg = Multiprocessed(tests).run()

    print('-' * 80)
    if thread_avg < process_avg:
        print('Threading is faster.')
    else:
        print('Multiprocessing is faster.')