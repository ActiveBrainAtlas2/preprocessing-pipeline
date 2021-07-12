def compare_lists(l1,l2):
    diff = set(l1)-set(l2)
    if diff != set():
        print('in l1 not l2')
        print(diff)
    diff = set(l2)-set(l1)
    if diff != set():
        print('in l2 not l1')
        print(diff)
