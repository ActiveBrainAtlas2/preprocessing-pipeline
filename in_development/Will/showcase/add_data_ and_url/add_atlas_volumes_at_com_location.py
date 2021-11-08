from lib.UrlGenerator import UrlGenerator
from lib.sqlcontroller import SqlController
controller = SqlController('DK52')
animals = controller.get_annotated_animals()
for animali in animals:
    title = animali + ' Atlas Volumes at COM Position'
    controller.delete_url(title = title,person_id = 34)
    generator = UrlGenerator()
    generator.add_stack_image(animali,channel=1)
    generator.add_segmentation_layer(folder_name = animali+' manual',layer_name = animali+' manual')   
    generator.add_annotation_layer('Manual')
    generator.add_to_database(title =title ,person_id = 34)
