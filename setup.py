# -*- coding: utf8 -*-

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://www.wtfpl.net/ for more details.

import setuptools


setuptools.setup(
    name="MentalXr",
    version="1.0",
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=True,
    author="Nicolas Spycher, Simon Marti",
    author_email="simon@marti.email",
    install_requires=("requests", "beautifulsoup4", "gevent",
                      "grequests", "Unidecode"),
    entry_points={
        'console_scripts': (
            "mentalxr = mentalxr:main",
        )
    },
)
