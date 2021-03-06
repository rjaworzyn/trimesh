import numpy as np

from ..points          import transform_points
from ..grouping        import group_rows
from ..transformations import rotation_matrix
from .transforms       import TransformForest

from .. import util


from collections import deque

class Scene:
    '''
    A simple scene graph which can be rendered directly via pyglet/openGL,
    or through other endpoints such as a raytracer. 

    Meshes and lights are added by name, which can then be moved by updating
    transform in the transform tree. 
    '''

    def __init__(self, 
                 node       = None,
                 base_frame ='world'):

        # instance name : mesh name
        self.nodes = {}
        self._cache = util.Cache(id_function=self.md5)

        # mesh name : Trimesh object
        self.meshes     = {}
        self.flags      = {}
        self.transforms = TransformForest(base_frame = base_frame)

        if node is not None:
            self.add_mesh(node)
            self.set_camera()
            
        self._cache.id_set()

    def add_mesh(self, mesh):
        '''
        Add a mesh to the scene.

        If the mesh has multiple transforms defined in its metadata, 
        a new instance of the mesh will be created at each transform. 
        '''        
        if util.is_sequence(mesh):
            for i in mesh:
                self.add_mesh(i)
            return

        if 'name' in mesh.metadata: 
            name_mesh = mesh.metadata['name']
        else:
            name_mesh = 'mesh_' + str(len(self.meshes))

        self.meshes[name_mesh] = mesh

        if 'transforms' in mesh.metadata:
            transforms = np.array(mesh.metadata['transforms'])
        else:
            transforms = np.eye(4).reshape((-1,4,4))

        for i, transform in enumerate(transforms):
            name_node = name_mesh + '_' + str(i)
            self.nodes[name_node] = name_mesh
            self.flags[name_node] = {'visible':True}
            self.transforms.update(frame_to = name_node, 
                                   matrix   = transform)

    def md5(self):
        '''
        MD5 of scene, which will change when meshes or transforms are changed
        '''
        mesh_hash = util.md5_object(np.sort([hash(i) for i in self.meshes.values()]))
        result = mesh_hash + self.transforms.md5()
        return result

    @util.cache_decorator
    def bounds(self):
        '''
        Return the overall bounding box of the scene.

        Returns
        --------
        bounds: (2,3) float points for min, max corner
        '''
        corners = deque()
        for instance, mesh_name in self.nodes.items():
            transform = self.transforms.get(instance)
            corners.append(transform_points(self.meshes[mesh_name].bounds, 
                                            transform))
        corners = np.vstack(corners)
        bounds  = np.array([corners.min(axis=0), 
                            corners.max(axis=0)])
        return bounds

    @util.cache_decorator
    def extents(self):
        return np.diff(self.bounds, axis=0).reshape(-1)

    @util.cache_decorator
    def scale(self):
        return self.extents.max()

    @util.cache_decorator
    def centroid(self):
        '''
        Return the center of the bounding box for the scene.

        Returns
        --------
        centroid: (3) float point for center of bounding box
        '''
        centroid = np.mean(self.bounds, axis=0)
        return centroid

    def duplicate_nodes(self):
        '''
        Return a sequence of node keys, where all keys in the group will
        be of the same mesh
        '''
        mesh_ids  = {k : m.identifier for k, m in self.meshes.items()}
        
        node_keys = np.array(list(self.nodes.keys()))
        node_ids  = [mesh_ids[v] for v in self.nodes.values()]
        
        node_groups = group_rows(node_ids, digits=1)

        duplicates  = [node_keys[g].tolist() for g in node_groups]
        return duplicates

    def set_camera(self, angles=None, distance=None, center=None):
        if center is None:
            center = self.centroid
        if distance is None:
            distance = self.extents.max()
        if angles is None:
            angles = np.zeros(3)

        translation        = np.eye(4)
        translation[0:3,3] = center
        translation[2][3] += distance*1.5

        transform = np.dot(rotation_matrix(angles[0], [1,0,0], point=center),
                           rotation_matrix(angles[1], [0,1,0], point=center))
        transform = np.dot(transform, translation)

        self.transforms.update(frame_from = 'camera', 
                               frame_to   = self.transforms.base_frame,
                               matrix     = transform)

    def dump(self):
        '''
        Append all meshes in scene to a list of meshes.
        '''
        result = deque()
        for node_id, mesh_id in self.nodes.items():
            transform = self.transforms.get(node_id)
            current   = self.meshes[mesh_id].copy()
            current.transform(transform)
            result.append(current)
        return np.array(result)

    def export(self, file_type='dict64'):
        '''
        Export a snapshot of the current scene.

        Arguments
        ----------
        file_type: what encoding to use for meshes
                   ie: dict, dict64, stl
        
        Returns
        ----------
        export: dict with keys:
                meshes: list of meshes, encoded as per file_type
                transforms: edge list of transforms, eg:
                             ((u, v, {'matrix' : np.eye(4)}))
        '''
        export = {'transforms' : self.transforms.export(),
                  'nodes'      : self.nodes,
                  'meshes'     : {},
                  'scene_cache' : self._cache.cache}
        # if the mesh has an export method use it, otherwise put the mesh
        # itself into the export object
        for node, mesh in self.meshes.items():
            if hasattr(mesh, 'export'): 
                export['meshes'][node] = mesh.export(file_type=file_type)
            else: 
                export['meshes'][node] = mesh
        return export
        
    def save_image(self, file_obj, resolution=(1024,768), **kwargs):
        from .viewer import SceneViewer
        SceneViewer(self, 
                    save_image = file_obj, 
                    resolution = resolution, 
                    **kwargs)

    def explode(self, vector=[0.0,0.0,1.0], origin=None):
        '''
        Explode a scene around a point and vector.
        '''
        if origin is None:
            origin = self.centroid
        centroids = np.array([self.meshes[i].centroid for i in self.nodes.values()])

        if np.shape(vector) == (3,):
            vectors = np.tile(vector, (len(centroids), 1))
            projected = np.dot(vector, (centroids-origin).T)
            offsets = vectors * projected.reshape((-1,1))
        elif isinstance(vector, float):
            offsets = (centroids-origin) * vector
        else:
            raise ValueError('Explode vector must by (3,) or float')

        for offset, node_key in zip(offsets, self.nodes.keys()):
            current = self.transforms[node_key]
            current[0:3,3] += offset
            self.transforms[node_key] = current

    def show(self, block=True, **kwargs):
        # this imports pyglet, and will raise an ImportError
        # if pyglet is not available 
        from .viewer import SceneViewer

        def viewer():
            SceneViewer(self, **kwargs)

        if block:
            viewer()
        else:
            from threading import Thread
            Thread(target = viewer, kwargs=kwargs).start()
