import unittest
from utm_projection.projection import check_utm_epsg,utm_finder,raster_projection,vector_projection

class TestProjection(unittest.TestCase):
    def test_check_utm_epsg(self):
        self.assertEqual(check_utm_epsg(), "Test check_utm_epsg function !")
        
    def test_utm_finder(self):
        self.assertEqual(utm_finder(), "Test utm_finder function !")
        
    def test_raster_projection(self):
        self.assertEqual(raster_projection(), "Test raster_projection function !")
        
    def test_vector_projection(self):
        self.assertEqual(vector_projection(), "Test vector_projection function !")

if __name__ == '__main__':
    unittest.main()