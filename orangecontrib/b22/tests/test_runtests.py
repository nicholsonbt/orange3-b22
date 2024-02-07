import unittest
import io
import sys

from orangecontrib.b22.tests.utils import nostderr, TestRunner, ExampleValidTest, ExampleInvalidTest




class RunTestsTest(unittest.TestCase):
    def test_init_empty(self):
        runner = TestRunner()
        self.assertListEqual(runner.test_classes, [])


    def test_init_single(self):
        runner = TestRunner(ExampleValidTest)
        self.assertListEqual(runner.test_classes, [ExampleValidTest])

    
    def test_init_multiple(self):
        runner = TestRunner([ExampleValidTest])
        self.assertListEqual(runner.test_classes, [ExampleValidTest])

    
    def test_add_single(self):
        runner = TestRunner()
        runner.addTestClasses(ExampleValidTest)
        self.assertListEqual(runner.test_classes, [ExampleValidTest])


    def test_add_multiple(self):
        runner = TestRunner()
        runner.addTestClasses([ExampleValidTest])
        self.assertListEqual(runner.test_classes, [ExampleValidTest])


    def test_add_existing(self):
        runner = TestRunner(ExampleValidTest)
        runner.addTestClasses(ExampleValidTest)
        self.assertListEqual(runner.test_classes, [ExampleValidTest, ExampleValidTest])

    
    def test_valid_single(self):
        with nostderr():
            runner = TestRunner(ExampleValidTest)
            result = runner.run()

        self.assertEqual(result.wasSuccessful(), True)

    
    def test_invalid_single(self):
        with nostderr():
            runner = TestRunner(ExampleInvalidTest)
            result = runner.run()

        self.assertEqual(result.wasSuccessful(), False)


    def test_valid_multiple(self):
        with nostderr():
            runner = TestRunner([ExampleValidTest, ExampleValidTest])
            result = runner.run()

        self.assertEqual(len(result.failures), 0)
        self.assertEqual(result.wasSuccessful(), True)

    
    def test_invalid_multiple(self):
        with nostderr():
            runner = TestRunner([ExampleInvalidTest, ExampleInvalidTest])
            result = runner.run()

        self.assertEqual(len(result.failures), 2)
        self.assertEqual(result.wasSuccessful(), False)


    def test_valid_invalid(self):
        with nostderr():
            runner = TestRunner([ExampleValidTest, ExampleInvalidTest])
            result = runner.run()

        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.wasSuccessful(), False)

    
    def test_verbose_0(self):
        original_stderr = sys.stderr
        output = io.StringIO()
        sys.stderr = output

        runner = TestRunner([ExampleValidTest, ExampleInvalidTest], verbosity=0)
        runner.run()

        sys.stderr = original_stderr

        lines = output.getvalue().split("\n")
    
        self.assertEqual(lines[0][0], "=")


    def test_verbose_1(self):
        original_stderr = sys.stderr
        output = io.StringIO()
        sys.stderr = output

        runner = TestRunner([ExampleValidTest, ExampleInvalidTest], verbosity=1)
        runner.run()

        sys.stderr = original_stderr

        lines = output.getvalue().split("\n")
    
        self.assertEqual(lines[0], ".F")
        self.assertEqual(lines[1][0], "=")


    def test_verbose_2(self):
        original_stderr = sys.stderr
        output = io.StringIO()
        sys.stderr = output

        runner = TestRunner([ExampleValidTest, ExampleInvalidTest], verbosity=2)
        runner.run()

        sys.stderr = original_stderr

        lines = output.getvalue().split("\n")
    
        self.assertEqual(lines[0], "test_example (orangecontrib.b22.tests.utils.ExampleValidTest.test_example) ... ok")
        self.assertEqual(lines[1], "test_example (orangecontrib.b22.tests.utils.ExampleInvalidTest.test_example) ... FAIL")
        self.assertEqual(lines[3][0], "=")


    def test_default_verbosity(self):
        runner = TestRunner(ExampleValidTest)
        self.assertEqual(runner.verbosity, 2)




if __name__ == "__main__":
    runner = TestRunner(RunTestsTest)
    result = runner.run()
