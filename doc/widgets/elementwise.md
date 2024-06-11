Elementwise Operations
======================

Perform elementwise operations (addition, subtraction, division and multiplication) on the attributes of two data tables.

**Inputs**

- Primary Data: data set used as *operand 1*
- Secondary Data: data set used as *operand 2*

**Outputs**

- Data: The result of \<*operand 1*\> \<*operator*\> \<*operand 2*\>

The widget performs elementwise operations on the attributes given two operand tables. Meta and target data are merged in the resulting data set.

**Image and Components**

1. Information on *operand 1*.
2. Information on *operand 2*.
3. Elementwise *operator*.


Example
-------

Here is a simple example on how to use the **Elementwise Operations** widget...


Notes
-----

**Valid Shapes**

If a row or column length is equal to 1 for either *operand 1* or *operand 2*, it will be broadcast to the size of the other operand.

| *Operand 1* | *Operand 2* |
| :---------: | :---------: |
| (n, m)      | (n, m)      |
| (n, m)      | (n, 1)      |
| (n, m)      | (1, m)      |
| (n, m)      | (1, 1)      |
| (1, m)      | (n, m)      |
| (n, 1)      | (n, m)      |
| (1, 1)      | (n, m)      |
| (n, 1)      | (1, m)      |
| (1, m)      | (n, 1)      |

\**Assuming n, m >= 1*

**Attribute Data**

If *operand 1* and *operand 2* have the same number of attributes (columns), the attribute variable names of *operand 1* will be used in the output table. Otherwise, the names will be taken from the operand with the most columns.

All attribute data must be continuous.

**Meta Data**

The meta data values are merged with duplicated names being renamed. The meta data of the operand with attribute variables used for the output table will be added first, with the meta data of the other operand added afterwards.

**Target Data**

Only one (or none) target variable is allowed in the output table, meaning the operands combined can contain only one target variable at most.

