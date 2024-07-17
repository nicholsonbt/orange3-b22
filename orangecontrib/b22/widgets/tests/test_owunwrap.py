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

from orangecontrib.b22.widgets.owunwrap import OWUnwrap




class TestOWUnwrap(WidgetTest):
    def setUp(self):
        self.iris = Table("iris")
        self.widget = self.create_widget(OWUnwrap)


    def test_default_autocommit_value(self):
        self.assertEqual(self.widget.autocommit,
                         self.widget.controls.autocommit.isChecked())


    def test_autocommit_checkbox_changes_value(self):
        # Changing checked automatically changes autocommit.
        self.widget.controls.autocommit.setChecked(
            not self.widget.autocommit
        )

        self.assertEqual(
            self.widget.controls.autocommit.isChecked(),
            self.widget.autocommit
        )


    def test_default_in_data(self):
        self.assertIsNone(self.widget.data)


    def test_unwrap_row(self):
        data = np.array([0., 0.78, 1.57, 5.49, 6.22, 7.8, 6.17, 4., 2.95, 3.33])

        expected = np.unwrap(data)
        actual = OWUnwrap.unwrap_row(data)

        self.assertTrue(np.allclose(actual, expected))

    
    def test_unwrap_row_nans(self):
        from orangecontrib.b22.widgets.owunwrap import NaNElementException

        data = np.array([0., np.nan, 1.57, 5.49, 6.22, 7.8, 6.17, 4., 2.95, 3.33])

        with self.assertRaises(NaNElementException):
            OWUnwrap.unwrap_row(data)
        
    


if __name__ == "__main__":
    unittest.main()
