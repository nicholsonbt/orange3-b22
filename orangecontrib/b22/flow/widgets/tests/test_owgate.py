# Test methods with long descriptive names can omit docstrings
# pylint: disable=missing-docstring, abstract-method, protected-access
import unittest
from unittest.mock import patch, Mock

import numpy as np
from numpy.testing import assert_array_equal

from Orange.data import (
    Table, Domain, ContinuousVariable, DiscreteVariable, StringVariable
)
from Orange.widgets.tests.base import WidgetTest

from orangecontrib.b22.flow.widgets.owgate import OWGate


class TestOWGate(WidgetTest):
    def setUp(self):
        self.iris = Table("iris")
        self.zoo = Table("zoo")
        self.widget = self.create_widget(OWGate)


    def test_default_autocommit_value(self):
        self.assertEqual(self.widget.autocommit, self.widget.controls.autocommit.isChecked())


    def test_autocommit_checkbox_changes_value(self):
        # Changing checked automatically changes autocommit.
        self.widget.controls.autocommit.setChecked(not self.widget.autocommit)
        self.assertEqual(self.widget.controls.autocommit.isChecked(), self.widget.autocommit)


    def test_default_in_data(self):
        self.assertIsNone(self.widget.in_data)


    def test_default_out_data(self):
        self.assertIsNone(self.widget.out_data)


    def test_default_output(self):
        self.assertIsNone(self.get_output(self.widget.Outputs.data))


    def test_default_warning(self):
        self.assertFalse(self.widget.Warning.not_connected.is_shown())




class TestOWGateClosed(TestOWGate):
    def test_none_input_in_data(self):
        self.send_signal(self.widget.Inputs.data, None)
        self.assertIsNone(self.widget.in_data)


    def test_none_input_out_data(self):
        self.send_signal(self.widget.Inputs.data, None)
        self.assertIsNone(self.widget.out_data)


    def test_none_input_output(self):
        self.send_signal(self.widget.Inputs.data, None)
        self.assertIsNone(self.get_output(self.widget.Outputs.data))


    def test_none_input_warning(self):
        self.send_signal(self.widget.Inputs.data, None)
        self.assertFalse(self.widget.Warning.not_connected.is_shown())


    def test_object_input_in_data(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.assertEqual(self.widget.in_data, self.iris)


    def test_object_input_out_data(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.assertIsNone(self.widget.out_data)


    def test_object_input_output(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.assertIsNone(self.get_output(self.widget.Outputs.data))


    def test_object_input_warning(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.assertTrue(self.widget.Warning.not_connected.is_shown())


    def test_object_input_commit_in_data(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.commit_and_wait()
        self.assertEqual(self.widget.in_data, self.iris)


    def test_object_input_commit_out_data(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.commit_and_wait()
        self.assertEqual(self.widget.out_data, self.iris)


    def test_object_input_commit_output(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.commit_and_wait()
        self.assertEqual(self.get_output(self.widget.Outputs.data), self.iris)


    def test_object_input_commit_warning(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.commit_and_wait()
        self.assertFalse(self.widget.Warning.not_connected.is_shown())


    def test_object_input_disconnect_in_data(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, None)
        self.assertIsNone(self.widget.in_data)


    def test_object_input_disconnect_out_data(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, None)
        self.assertIsNone(self.widget.out_data)


    def test_object_input_disconnect_output(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, None)
        self.assertIsNone(self.get_output(self.widget.Outputs.data))


    def test_object_input_disconnect_warning(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, None)
        self.assertFalse(self.widget.Warning.not_connected.is_shown())


    def test_object_input_disconnect_commit_in_data(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, None)
        self.commit_and_wait()
        self.assertIsNone(self.widget.in_data)


    def test_object_input_disconnect_commit_out_data(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, None)
        self.commit_and_wait()
        self.assertIsNone(self.widget.out_data)


    def test_object_input_disconnect_commit_output(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, None)
        self.commit_and_wait()
        self.assertIsNone(self.get_output(self.widget.Outputs.data))


    def test_object_input_disconnect_commit_warning(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, None)
        self.commit_and_wait()
        self.assertFalse(self.widget.Warning.not_connected.is_shown())


    def test_object_input_commit_disconnect_in_data(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.commit_and_wait()
        self.send_signal(self.widget.Inputs.data, None)
        self.assertEqual(self.widget.in_data, None)


    def test_object_input_commit_disconnect_out_data(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.commit_and_wait()
        self.send_signal(self.widget.Inputs.data, None)
        self.assertEqual(self.widget.out_data, self.iris)


    def test_object_input_commit_disconnect_output(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.commit_and_wait()
        self.send_signal(self.widget.Inputs.data, None)
        self.assertEqual(self.get_output(self.widget.Outputs.data), self.iris)


    def test_object_input_commit_disconnect_warning(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.commit_and_wait()
        self.send_signal(self.widget.Inputs.data, None)
        self.assertTrue(self.widget.Warning.not_connected.is_shown())


    def test_object_input_commit_input_in_data(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.commit_and_wait()
        self.send_signal(self.widget.Inputs.data, self.zoo)
        self.assertEqual(self.widget.in_data, self.zoo)


    def test_object_input_commit_input_out_data(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.commit_and_wait()
        self.send_signal(self.widget.Inputs.data, self.zoo)
        self.assertEqual(self.widget.out_data, self.iris)


    def test_object_input_commit_input_output(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.commit_and_wait()
        self.send_signal(self.widget.Inputs.data, self.zoo)
        self.assertEqual(self.get_output(self.widget.Outputs.data), self.iris)


    def test_object_input_commit_input_warning(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.commit_and_wait()
        self.send_signal(self.widget.Inputs.data, self.zoo)
        self.assertTrue(self.widget.Warning.not_connected.is_shown())


    def test_object_input_input_commit_in_data(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, self.zoo)
        self.commit_and_wait()
        self.assertEqual(self.widget.in_data, self.zoo)


    def test_object_input_input_commit_out_data(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, self.zoo)
        self.commit_and_wait()
        self.assertEqual(self.widget.out_data, self.zoo)


    def test_object_input_input_commit_output(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, self.zoo)
        self.commit_and_wait()
        self.assertEqual(self.get_output(self.widget.Outputs.data), self.zoo)


    def test_object_input_input_commit_warning(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, self.zoo)
        self.commit_and_wait()
        self.assertFalse(self.widget.Warning.not_connected.is_shown())



class TestOWGateOpen(TestOWGate):
    def setUp(self):
        TestOWGate.setUp(self)
        self.widget.autocommit = True


    def test_none_input_out_data(self):
        self.send_signal(self.widget.Inputs.data, None)
        self.assertIsNone(self.widget.out_data)


    def test_none_input_output(self):
        self.send_signal(self.widget.Inputs.data, None)
        self.assertIsNone(self.get_output(self.widget.Outputs.data))


    def test_none_input_warning(self):
        self.send_signal(self.widget.Inputs.data, None)
        self.assertFalse(self.widget.Warning.not_connected.is_shown())


    def test_object_input_out_data(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.assertEqual(self.widget.out_data, self.iris)


    def test_object_input_output(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.assertEqual(self.get_output(self.widget.Outputs.data), self.iris)


    def test_object_input_warning(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.assertFalse(self.widget.Warning.not_connected.is_shown())


    def test_object_input_disconnect_out_data(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, None)
        self.assertIsNone(self.widget.out_data)


    def test_object_input_disconnect_output(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, None)
        self.assertIsNone(self.get_output(self.widget.Outputs.data))


    def test_object_input_disconnect_warning(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, None)
        self.assertFalse(self.widget.Warning.not_connected.is_shown())


    def test_object_input_input_in_data(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, self.zoo)
        self.assertEqual(self.widget.in_data, self.zoo)


    def test_object_input_input_out_data(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, self.zoo)
        self.assertEqual(self.widget.out_data, self.zoo)


    def test_object_input_input_output(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, self.zoo)
        self.assertEqual(self.get_output(self.widget.Outputs.data), self.zoo)


    def test_object_input_input_warning(self):
        self.send_signal(self.widget.Inputs.data, self.iris)
        self.send_signal(self.widget.Inputs.data, self.zoo)
        self.assertFalse(self.widget.Warning.not_connected.is_shown())




if __name__ == "__main__":
    unittest.main()