from pipeline.Controllers.UrlController import UrlController
import json
from pipeline.lib.annotation_layer import AnnotationLayer
name='Starter outside of 12n'
controller = UrlController()
urls = controller.get_url_id_list()
for id in urls:
    url = controller.get_urlModel(id)
    names = [i['name'] for i in json.loads(url.url)['layers']]
    # print(id,names)
    if name in names:
        print(id)