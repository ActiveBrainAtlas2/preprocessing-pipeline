import SimpleITK as sitk

class RegistrationStatusReport():
    def __init__(self,registration_method):
        self.registration_method = registration_method

    def set_report_events(self):
        """set_report_events [sets the events for reporting the status of the registeration]
        """
        self.registration_method.AddCommand(sitk.sitkStartEvent, start_optimization)
        self.registration_method.AddCommand(sitk.sitkIterationEvent, 
        lambda: self.print_values())
        self.registration_method.AddCommand(sitk.sitkMultiResolutionIterationEvent,
         report_multi_resolution_events)
    

    def print_values(self):
        global n_iter
        n_iter+=1
        if n_iter%10 == 0 :
            print(f'iteration: {n_iter} {self.registration_method.GetMetricValue():4f}')

def report_multi_resolution_events():
    global n_iter,n_resolution
    n_iter=0
    if n_resolution !=0:
        print('switching to higher resolution')
    elif n_resolution == 0:
        print('starting optimization')
    n_resolution+=1

def start_optimization():
    global n_resolution
    n_resolution = 0