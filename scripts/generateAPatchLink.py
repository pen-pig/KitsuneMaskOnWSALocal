#!/usr/bin/python3
#
# This file is part of MagiskOnWSALocal.
#
# MagiskOnWSALocal is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# MagiskOnWSALocal is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with MagiskOnWSALocal.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright (C) 2024 LSPosed Contributors
#

import sys
import os
from typing import Any, OrderedDict
from pathlib import Path


class Prop(OrderedDict):
    def __init__(self, props: str = ...) -> None:
        super().__init__()
        for i, line in enumerate(props.splitlines(False)):
            if '=' in line:
                k, v = line.split('=', 1)
                self[k] = v
            else:
                self[f".{i}"] = line

    def __setattr__(self, __name: str, __value: Any) -> None:
        self[__name] = __value

    def __repr__(self):
        return '\n'.join(f'{item}={self[item]}' for item in self)


arch = sys.argv[1]
arg2 = sys.argv[2]
download_dir = Path.cwd().parent / "download" if arg2 == "" else Path(arg2)
tempScript = sys.argv[3]
kernelVersion = sys.argv[4]
file_name = sys.argv[5]
abi_map = {"x64": "x86_64", "arm64": "arm64"}

# APatch custom mode: look for custom patched kernel zip in download directory
# Format: apatch-WSA-{arch}-{kernel_version}.zip or generic apatch.zip
# The zip must contain a kernel file (bzImage for x64, Image for arm64)
expected_name = f"apatch-WSA-{abi_map[arch]}-{kernelVersion}.zip"
target = download_dir / file_name  # Expected: kernelsu-{arch}-{kernel_version}.zip

print(
    f"Searching for APatch custom kernel: expected={expected_name}", flush=True)

found = False
# Check exact match first: apatch-WSA-{arch}-{kernelVer}.zip
exact = download_dir / expected_name
if exact.exists():
    print(f"Found exact match: {exact.name}", flush=True)
    if exact.resolve() != target.resolve():
        exact.rename(target)
    found = True
else:
    # Check for any apatch-WSA-*.zip
    for f in sorted(download_dir.iterdir()):
        if f.is_file() and f.name.startswith("apatch-WSA-") and f.name.endswith(".zip"):
            print(f"Found APatch kernel: {f.name}", flush=True)
            if f.resolve() != target.resolve():
                f.rename(target)
            found = True
            break

if not found:
    # Fallback: apatch.zip
    fallback = download_dir / "apatch.zip"
    if fallback.exists():
        print(f"Using fallback: apatch.zip", flush=True)
        if fallback.resolve() != target.resolve():
            fallback.rename(target)
        found = True

if not found:
    print(
        f"Error: No APatch kernel zip found. Place {expected_name} (or apatch.zip) in {download_dir}. "
        f"The zip must contain a kernel file (bzImage for x64, Image for arm64).",
        flush=True)
    exit(1)

# Set version info
print(f"APatch kernel ready: {target.name}", flush=True)
release_name = "custom"
with open(os.environ['WSA_WORK_ENV'], 'r') as environ_file:
    env = Prop(environ_file.read())
    env.KERNELSU_VER = release_name
with open(os.environ['WSA_WORK_ENV'], 'w') as environ_file:
    environ_file.write(str(env))

# Do NOT write to download conf - file is already local, no aria2c needed
