import generic as g

class BooleanTest(g.unittest.TestCase):
    def setUp(self):
        e = g.trimesh.primitives.Extrusion()
        e.extrude_polygon = g.trimesh.path.polygons.random_polygon()
        e.extrude_height = 1.0

        self.primitives = [e]
        self.primitives.append(g.trimesh.primitives.Extrusion(extrude_polygon=g.trimesh.path.polygons.random_polygon(),
                                                              extrude_height = 293292.322))
        self.primitives.append(g.trimesh.primitives.Sphere())
        self.primitives.append(g.trimesh.primitives.Sphere(sphere_center=[0,0,100], 
                                                           sphere_radius=10.0, 
                                                           subdivisions=5))
        self.primitives.append(g.trimesh.primitives.Box())
        self.primitives.append(g.trimesh.primitives.Box(box_center=[102.20,0,102.0],
                                                        box_extents = [29,100,1000]))
    def test_primitives(self):
        for primitive in self.primitives:
            self.assertTrue(g.trimesh.util.is_shape(primitive.faces,    (-1,3)))
            self.assertTrue(g.trimesh.util.is_shape(primitive.vertices, (-1,3)))

            self.assertTrue(primitive.volume > 0.0)

            self.assertTrue(primitive.is_winding_consistent)
            self.assertTrue(primitive.is_watertight)

if __name__ == '__main__':
    g.trimesh.util.attach_to_log()
    g.unittest.main()
    
