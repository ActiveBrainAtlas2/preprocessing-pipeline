## Class: Django
  Very simply, Django provides us the bridge between Neuroglancer and the database. This is mainly done via Django's very powerful and popular
  REST framework. This framework follows the MVC (model, view, controller) design pattern. Django breaks down the MVC framework into modular 'apps'.
  The apps are listed below with a description the the classes that make up the models, views and controllers for each app. Apps for CVAT, User, and
  authentication have not been included as they are not created by us.
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
            1. (Taken care of by Neuroglancer)
        1. Controllers
            1. Animal
    1. Neuroglancer
        1. Models
            1. AlignmentScore
            1. AnnotationAbstract - Abstract class describing the 3 separate annotation classes:
                1. MarkedCell - annotated cells marked by an anatomist.
                1. PolygonSequence - sets of polygons drawn by an anatomist.
                1. StructureCom - Centers of mass for a given structure.
            1. AnnotationPointArchive - the archived annotation data
            1. AnnotationSession - Metadata describing a session of annotations performed by a user.
            1. ArchiveSet - metadata describing the archived annotation data
            1. BrainRegion - Formerly called structure, this represents an area of the brain.
            1. BrainShape - class for the numpy 3D masks
            1. UrlModel - This is the class that takes care of the Neuroglancer JSON state.

        1. Views
            1. (Taken care of by Neuroglancer)
        1. Controllers (REST API)
            1. UrlViewSet - allows creation, retrieval, updating of Neuroglancer JSON data 
            1. AlignAtlasView - used by the alignment process to create a rigid transformation
            1. Annotation - deals with one set of annotations
            1. Annotations - fetches all sets of annotations
            1. Rotation - deals with one rotation
            1. Rotations - fetches all sets of rotations
