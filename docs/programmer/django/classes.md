## Class: Django
  Very simply, Django provides us the bridge between Neuroglancer and the database. This is mainly done via Django's very powerful and popular
  REST framework. This framework follows the MVC (model, view, controller) design pattern. Django breaks down the MVC framework into modular 'apps'.
  The apps are listed below with a description the the classes that make up the models, views and controllers for each app.
1. Apps
    1. Brain
        1. Models
            1.  AtlasModel:
            1.  Animal
            1.  FileOperation
            1.  Histology
            1.  Injection
            1.  InjectionVirus
            1.  OrganicLabel
            1.  ScanRun
            1.  Slide
            1.  SlideCziToTif
            1.  Section

        1. Views
            1. Animal
        1. Controllers
    1. CVAT
        1. Models
        1. Views
        1. Controllers
    1. Neuroglancer
        1. Models
        1. Views
        1. Controllers
