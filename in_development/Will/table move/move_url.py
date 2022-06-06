from abakit.lib.Controllers.UrlController import UrlController
from abakit.model.urlModel import UrlModel

development_controller = UrlController(schema='active_atlas_development')
production_controller = UrlController(schema='active_atlas_production')

url = development_controller.get_urlModel(508)
production_controller.add_url(content = url.url,title = url.comments,person_id=34)