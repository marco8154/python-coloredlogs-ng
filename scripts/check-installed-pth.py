#!/usr/bin/env python

"""
Check the installed ``coloredlogs.pth`` file (used by the continuous integration).

Python executes ``*.pth`` files in the ``site-packages`` directory during the
startup of every process, so this file deserves extra attention. The checks:

1. The file is installed in a ``site-packages`` directory.
2. Its contents are byte for byte what coloredlogs 15.0.1 shipped.
3. Without ``$COLOREDLOGS_AUTO_INSTALL`` nothing is imported at startup.
4. With ``$COLOREDLOGS_AUTO_INSTALL=1`` a handler is attached to the root logger.

Run this from a directory that doesn't contain the source tree, using the
Python interpreter of the environment where the wheel was installed.
"""

import hashlib
import os
import site
import subprocess
import sys

#: SHA-256 of the ``coloredlogs.pth`` file in coloredlogs 15.0.1 on PyPI.
EXPECTED_SHA256 = 'dda83a855986efa5cd87f0248b0199c0086eb0e8e7fece7d6741959c5ce39536'


def run(code, **environment):
    """Run Python code in a fresh interpreter and return its standard output."""
    env = dict(os.environ)
    env.pop('COLOREDLOGS_AUTO_INSTALL', None)
    env.update(environment)
    return subprocess.check_output([sys.executable, '-c', code], env=env, universal_newlines=True).strip()


def main():
    """Perform the checks, exit with a nonzero status when one of them fails."""
    candidates = [os.path.join(directory, 'coloredlogs.pth') for directory in site.getsitepackages()]
    installed = [pathname for pathname in candidates if os.path.isfile(pathname)]
    assert len(installed) == 1, "Expected exactly one installed coloredlogs.pth file, found %r!" % installed
    with open(installed[0], 'rb') as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()
    assert digest == EXPECTED_SHA256, "Unexpected contents of %s! (SHA-256: %s)" % (installed[0], digest)
    loaded = run("import sys; print('coloredlogs' in sys.modules, 'humanfriendly' in sys.modules)")
    assert loaded == 'False False', "Modules were imported at startup without the environment variable! (%s)" % loaded
    handlers = run(
        "import logging; print([type(h).__name__ for h in logging.getLogger().handlers])",
        COLOREDLOGS_AUTO_INSTALL='1',
    )
    assert handlers == "['StandardErrorHandler']", "Unexpected root handlers with auto install enabled! (%s)" % handlers
    print("coloredlogs.pth is installed, unchanged and behaves as expected: %s" % installed[0])


if __name__ == '__main__':
    main()
