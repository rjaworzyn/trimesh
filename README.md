# trimesh #
[![Build Status](https://travis-ci.org/mikedh/trimesh.svg?branch=master)](https://travis-ci.org/mikedh/trimesh)

Python (2.7-3*) library for loading and using triangular meshes. The goal of the library is to provide a fully featured Trimesh object which allows for easy manipulation and analysis, in the style of the excellent Polygon object in the Shapely library.

The API is mostly stable, but this should not be relied on and is not guaranteed; install a specific version if you plan on deploying something using trimesh as a backend.

### Installation ###

The easiest way to install with most functionality is:
```bash
$ sudo apt-get install cmake openscad blender libspatialindex-dev libgeos-dev
$ sudo pip install trimesh[all]
```

Or, for only minimal dependencies (no ray queries, boolean operations, vector path handling, mesh creation, viewer, etc):

```bash
$ sudo pip install trimesh
```

The minimum set of packages required to import `trimesh` are
[numpy](http://www.numpy.org/), [scipy](http://www.scipy.org/) and [networkx](https://networkx.github.io/). 

### Optional Dependencies ###

To get the latest assimp for [additional import formats](http://www.assimp.org/main_features_formats.html) (python-pyassimp in Ubuntu 14.04 is very old):

```bash
$ sudo pip install git+https://github.com/robotics/assimp_latest.git
```

If you are using a lot of graph operations (specifically mesh.split) trimesh will automatically use [graph-tool](https://graph-tool.skewed.de/download) if it is installed, for a roughly 10x speedup over networkx on certain operations.


### Features ###

* Import binary/ASCII STL, Wavefront OBJ, ASCII OFF, and binary PLY
* Import additional mesh formats using assimp (if pyassimp installed)
* Import STEP files as meshes (if STEPtools Inc. Author Tools installed)
* Import and export 2D or 3D vector paths from/to DXF or SVG files
* Export meshes as binary STL, binary PLY, ASCII OFF, COLLADA, dictionaries, JSON- serializable dictionaries (base64 encoded arrays), MSGPACK- serializable dictionaries (binary string arrays)
* Preview meshes (requires pyglet)
* Internal caching of computed values which are automatically cleared when vertices or faces are changed (which we know from a lazily evaluated MD5)
* Fast loading of binary files through importers written by defining custom numpy dtypes ( on a 234,230 face mesh, 24.5x faster than assimp)
* Calculate face adjacencies quickly (for the same 234,230 face mesh .248 s)
* Calculate cross sections (.146 s)
* Split mesh based on face connectivity using networkx (4.96 s) or graph-tool (.584 s)
* Calculate mass properties, including volume, center of mass, and moment of inertia (.246 s)
* Find coplanar groups of faces (.454 s)
* Fix triangle winding to be consistent (slow)
* Fix normals to be oriented 'outwards' using ray tests
* Calculate whether or not a point lies inside a watertight mesh using ray tests
* Find convex hulls of meshes
* Compute a rotation/translation/tessellation invariant identifier for meshes (from an FFT of the radius distribution)
* Merge duplicate meshes from identifier
* Determine if a mesh is watertight (manifold)
* Repair single triangle and single quad holes
* Uniformly sample the surface of a mesh
* Ray-mesh intersection
* Boolean operations on meshes (intersection, union, difference) if OpenSCAD or blender is installed
* Voxelize watertight meshes
* Unit conversions
* Subdivide faces of a mesh
* Rapid computation of minimum- volume oriented bounding box transform for a mesh
* Symbolic integration of function(x,y,z) over a triangle
* Very quick (sympy-numpy lambda) evaluation of symbolic integral result over a mesh 
* Create meshes with primitive objects (Extrude, Box, Sphere) which are subclasses of Trimesh
* Simple scene graph and transform tree which can be rendered (pyglet) or exported.
* Numerous utility functions, such as transforming points, unitizing vectors, tracking arrays for changes, grouping rows, etc.

### Quick Start ###

Here is an example of loading a mesh from file and colorizing its faces. Here is a nicely formatted
[ipython notebook version](http://github.com/mikedh/trimesh/blob/master/examples/quick_start.ipynb) of this example.


```python
import numpy as np
import trimesh

# load a file by name or from a buffer
mesh = trimesh.load_mesh('../models/featuretype.STL')

# is the current mesh watertight?
mesh.is_watertight

# what's the euler number for the mesh?
mesh.euler_number

# the convex hull is another Trimesh object that is available as a property
# lets compare the volume of our mesh with the volume of its convex hull
np.divide(mesh.volume, mesh.convex_hull.volume)

# since the mesh is watertight, it means there is a
# volumetric center of mass which we can set as the origin for our mesh
mesh.vertices -= mesh.center_mass

# what's the moment of inertia for the mesh?
mesh.moment_inertia

# if there are multiple bodies in the mesh we can split the mesh by
# connected components of face adjacency
# since this example mesh is a single watertight body we get a list of one mesh
mesh.split()

# find groups of coplanar adjacent faces
facets, facets_area = mesh.facets(return_area=True)

# set each facet to a random color
# colors are 8 bit RGBA by default (n,4) np.uint8
for facet in facets:
    mesh.visual.face_colors[facet] = trimesh.visual.random_color()

# preview mesh in an opengl window if you installed pyglet with pip
mesh.show()

# transform method can be passed a (4,4) matrix and will cleanly apply the transform
mesh.apply_transform(trimesh.transformations.random_rotation_matrix())

# axis aligned bounding box is available
mesh.bounding_box.extents

# a minimum volume oriented bounding box also available
mesh.bounding_box_oriented.box_extents
mesh.bounding_box_oriented.box_transform

# show the mesh overlayed with its oriented bounding box
# the bounding box is a trimesh.primitives.Box object, which subclasses
# Trimesh and lazily evaluates to fill in vertices and faces when requested
# (press w in viewer to see triangles)
(mesh + mesh.bounding_box_oriented + mesh.bounding_box).show()
```

### Optional Viewer ###

Trimesh includes an optional pyglet- based viewer for debugging/inspecting. In the mesh view window:

* dragging rotates the view
* ctl + drag pans
* mouse wheel zooms
* 'z' returns to the base view 
* 'w' toggles wireframe mode
* 'c' toggles backface culling
