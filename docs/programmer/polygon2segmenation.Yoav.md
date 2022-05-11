Comments:
* Class can be extended to multiple classes, potentially with
  inheritence.
* What are listed here as classes might be expanded to modules containing
  multiple classes.


## Class: Database bridge
Connects to database back-end. Provides
interfaces for reading/writing/add/removing from the different tables.

Class should hide the details of the implementation (sqlalchemy,
MySQL,...) so that transitioning to a different database backend
requires changes only in this class and not in others.

## Class: 3DObject
implements different representations of a 3D object and
transformations between them:

* Polygon-Sequence
* 3DMask
* Encoded (compressed) 3DMask

## Class: Transformation
Implements transformations between coordinate systems. Sub-classes for
differen transformations (Rigid, Rigid+scaling, affine, b-spline, ...)

Methods

* transformPoints (points,to_atlas=True) transforms points to/from
  atlas coordinates.
* transform3DMask (3Dobject,to_atlas=True) transforms 3Dmask to/from
  atlas coordinates.
