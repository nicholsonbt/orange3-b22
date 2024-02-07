import unittest

from orangecontrib.b22.utils import loadHyperspectra




class LoadHyperspectraTest(unittest.TestCase):
    def setUp(self):
        self.table = loadHyperspectra()


    def test_loaded(self):
        self.assertIsNotNone(self.table)

    
    def test_shape(self):
        self.assertEqual(self.table.X.shape, (3250, 831))

    
    def test_metas(self):
        self.assertListEqual([attr.name for attr in self.table.domain.metas], ["map_x", "map_y"])




if __name__ == "__main__":
    from orangecontrib.b22.tests.utils import TestRunner
    runner = TestRunner(LoadHyperspectraTest)
    runner.run()
