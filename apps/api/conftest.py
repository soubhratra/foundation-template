"""
Root conftest.py for apps/api.

Sets DYLD_LIBRARY_PATH on macOS so WeasyPrint can find Homebrew-installed
system libraries (pango, glib, fontconfig). Linux Docker containers have
these installed at standard paths — no special configuration needed there.
"""

import os
import platform

if platform.system() == "Darwin":
    # Ensure Homebrew library path is included so WeasyPrint's cffi bindings
    # can load libgobject-2.0, libpango-1.0, etc.
    homebrew_lib = "/usr/local/lib"
    current = os.environ.get("DYLD_LIBRARY_PATH", "")
    if homebrew_lib not in current:
        paths = [homebrew_lib] + [p for p in current.split(":") if p]
        os.environ["DYLD_LIBRARY_PATH"] = ":".join(paths)
