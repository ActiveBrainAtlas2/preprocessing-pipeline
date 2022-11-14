from pipeline.Controllers.UrlController import UrlController
from pipeline.lib.annotation_layer import AnnotationLayer
from atlas.VolumeMaker import VolumeMaker
from atlas.NgSegmentMaker import NgConverter
import json
from pipeline.Controllers.TransformationController import TransformationController
from atlas.Assembler import Assembler
controller = UrlController()
transformation_controller = TransformationController()
urls = [312,336,343,345,462,468,502,503,505,506,507,508]
volumes = {}
downsample_factor = 100
def get_animal_id(neuroglancer_json):
    layers = [i for i in neuroglancer_json['layers'] if i['type']=='image']
    if len(layers)==0:
        return None
    elif len(layers)>=1:
        image_layer = layers[0]
        source = image_layer['source']
        if type(source)==dict:
            source = source['url']
        start_id = source.find('/data/')
        return source[start_id:].split('/')[2]
    else:
        raise NotImplementedError

for url_id in urls:
    url = controller.get_urlModel(url_id)
    neuroglancer_json = json.loads(url.url)
    animal_id = get_animal_id(neuroglancer_json)
    layers = [i for i in neuroglancer_json['layers'] if i['type']=='annotation' and i['name'] not in ['test','cell']]
    assert len(layers)
    layer = AnnotationLayer(layers[0])
    for annotation in layer.annotations:
        if annotation.description =='7N_R' and annotation.is_volume():
            name,contours = annotation.get_volume_name_and_contours(downsample_factor = downsample_factor)
            maker = VolumeMaker(animal_id)
            maker.set_aligned_contours({name:contours})
            maker.compute_COMs_origins_and_volumes()
            del maker.sqlController
            volumes[animal_id]=maker
animals_with_no_volume = []
for animal in volumes:
    if not transformation_controller.has_transformation(source=animal,destination='Atlas'):
        animals_with_no_volume.append(animal)
        continue
    transformation = transformation_controller.get_transformation(source=animal,destination='Atlas',transformation_type='Similarity')
    volumes[animal] = transformation.forward_transform_volume(volumes[animal],downsample_factor)
for animal in animals_with_no_volume:
    del volumes[animal] 

assembler = Assembler(check=False)
assembler.origins = {}
assembler.volumes = {}
for animal in volumes:
    assembler.origins[animal+'_7N_R'] = volumes[animal].origins['7N_R']
    assembler.volumes[animal+'_7N_R'] = volumes[animal].volumes['7N_R']
segment_to_id = {}
id =1
for segment in assembler.origins.keys():
    segment_to_id[segment]=id
    id+=1
assembler.structures = list(assembler.origins.keys())
assembler.assemble_all_structure_volume(segment_to_id)
converter = NgConverter(volume = assembler.combined_volume,scales=[0.325*downsample_factor*1000,0.325*downsample_factor*1000,20000])
segment_properties = [(i+1,list(volumes.keys())[i]) for i in range(len(volumes))]
converter.create_neuroglancer_files(output_dir=maker.path.segmentation_layer+'/compare_7N_R',segment_properties=segment_properties)
print('done')

