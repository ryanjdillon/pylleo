Building the documentation
==========================

napoleon
--------
The source code is documented using the Numpy documentation style, which
requires the extension napoleon for sphinx to correctly parse documentation
from the source code docstrings.

Install napoleon::

    pip install spinxcontrib-napoleon

See the end of the conf.py file to see the napoleon options for compiling.

Compiling
---------
Then you can build the documentation using the sphinx Makfile by running the
following in `pylleo`'s installation directory location::

    make html
