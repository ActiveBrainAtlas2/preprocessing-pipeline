def start_optimization():
    global n_resolution
    n_resolution = 0

def print_values(registration_method):
    global n_iter
    n_iter+=1
    if n_iter%10 == 0 :
        print(f'iteration: {n_iter} {registration_method.GetMetricValue():4f}')

def report_multi_resolution_events():
    global n_iter,n_resolution
    n_iter=0
    if n_resolution !=0:
        print('switching to higher resolution')
    elif n_resolution == 0:
        print('starting optimization')
    n_resolution+=1