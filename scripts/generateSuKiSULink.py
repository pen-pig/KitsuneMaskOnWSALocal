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

from datetime import datetime
import sys
import os
from typing import Any, OrderedDict

import requests
import json
import re
from pathlib import Path
from packaging import version


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
target = download_dir / file_name

# Phase 1: Try GitHub releases for pre-built WSA kernel
print(
    f"Generating SuKiSU download link: arch={abi_map[arch]}, kernel version={kernelVersion}", flush=True)
try:
    res = requests.get(
        f"https://api.github.com/repos/rifsxd/KernelSU-Next/releases/latest")
    json_data = json.loads(res.content)
    headers = res.headers
    x_ratelimit_remaining = headers.get("x-ratelimit-remaining", "")
    kernel_ver = "0"
    link = ""
    if res.status_code == 200:
        assets = json_data.get("assets", [])
        for asset in assets:
            asset_name = asset["name"]
            if re.match(r'kernel-WSA-' + abi_map[arch] + '-' + kernelVersion + r'.*\.zip$', asset_name) and asset["content_type"] == "application/zip":
                tmp_kernel_ver = re.search(
                    r'\d{1}\.\d{1,}\.\d{1,}\.\d{1,}', asset_name.split("-")[3]).group()
                if kernel_ver == "0":
                    kernel_ver = tmp_kernel_ver
                elif version.parse(kernel_ver) < version.parse(tmp_kernel_ver):
                    kernel_ver = tmp_kernel_ver
        print(f"Kernel version: {kernel_ver}", flush=True)
        for asset in assets:
            if re.match(r'kernel-WSA-' + abi_map[arch] + '-' + kernel_ver + r'.*\.zip$', asset["name"]) and asset["content_type"] == "application/zip":
                link = asset["browser_download_url"]
                break
    if link:
        release_name = json_data["name"]
        with open(os.environ['WSA_WORK_ENV'], 'r') as environ_file:
            env = Prop(environ_file.read())
            env.KERNELSU_VER = release_name
        with open(os.environ['WSA_WORK_ENV'], 'w') as environ_file:
            environ_file.write(str(env))
        print(f"download link: {link}", flush=True)
        with open(download_dir / tempScript, 'a') as f:
            f.writelines(f'{link}\n')
            f.writelines(f'  dir={download_dir}\n')
            f.writelines(f'  out={file_name}\n')
        exit(0)
except Exception as e:
    print(f"GitHub API error: {e}", flush=True)

# Phase 2: Custom fallback - look for kernel-WSA-*.zip or sukisu.zip in download directory
print("No WSA kernel found in SuKiSU releases. Trying custom kernel...", flush=True)
found = False
for f in sorted(download_dir.iterdir()):
    if f.is_file() and f.name.startswith("kernel-WSA-") and f.name.endswith(".zip"):
        print(f"Found custom kernel: {f.name}", flush=True)
        if f.resolve() != target.resolve():
            f.rename(target)
        found = True
        break

if not found:
    # Fallback: sukisu.zip
    fallback = download_dir / "sukisu.zip"
    if fallback.exists():
        print(f"Using fallback: sukisu.zip", flush=True)
        if fallback.resolve() != target.resolve():
            fallback.rename(target)
        found = True

if not found:
    print(
        f"Error: No SuKiSU kernel found. Place kernel-WSA-{abi_map[arch]}-{kernelVersion}.zip "
        f"or sukisu.zip in {download_dir}. The zip must contain a kernel file (bzImage for x64, Image for arm64).",
        flush=True)
    exit(1)

# Custom mode: set version and skip aria2c (no conf file entry)
release_name = "custom"
with open(os.environ['WSA_WORK_ENV'], 'r') as environ_file:
    env = Prop(environ_file.read())
    env.KERNELSU_VER = release_name
with open(os.environ['WSA_WORK_ENV'], 'w') as environ_file:
    environ_file.write(str(env))

print(f"Custom kernel ready: {target.name}", flush=True)
# Do NOT write to aria2c conf - file is already local
