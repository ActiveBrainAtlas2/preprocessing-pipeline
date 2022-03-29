from lib.SqlController import SqlController
controller = SqlController('DK52')
a = controller.get_com_dict('DK52')
print(a)