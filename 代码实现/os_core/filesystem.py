#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件系统模块
File System Module
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class VirtualFile:
    """虚拟文件"""
    name: str
    content: bytes = b""
    position: int = 0

    def read(self, size: int) -> bytes:
        data = self.content[self.position:self.position + size]
        self.position += len(data)
        return data

    def write(self, data: bytes) -> int:
        before = self.content[:self.position]
        after = self.content[self.position + len(data):]
        self.content = before + data + after
        self.position += len(data)
        return len(data)


class VirtualFileSystem:
    """虚拟文件系统"""

    def __init__(self):
        self.files: Dict[str, VirtualFile] = {}
        self.open_files: Dict[int, VirtualFile] = {}
        self.next_fd = 3

        # 标准流
        self.files["stdin"] = VirtualFile("stdin")
        self.files["stdout"] = VirtualFile("stdout")
        self.files["stderr"] = VirtualFile("stderr")
        self.open_files[0] = self.files["stdin"]
        self.open_files[1] = self.files["stdout"]
        self.open_files[2] = self.files["stderr"]

    def create_file(self, filename: str, content: bytes = b"") -> bool:
        if filename in self.files:
            return False
        self.files[filename] = VirtualFile(filename, content)
        return True

    def open_file(self, filename: str) -> int:
        if filename not in self.files:
            return -1
        fd = self.next_fd
        self.next_fd += 1
        self.open_files[fd] = self.files[filename]
        return fd

    def close_file(self, fd: int) -> int:
        if fd not in self.open_files or fd < 3:
            return -1
        del self.open_files[fd]
        return 0

    def read_file(self, fd: int, size: int) -> Optional[bytes]:
        if fd not in self.open_files:
            return None
        return self.open_files[fd].read(size)

    def write_file(self, fd: int, data: bytes) -> int:
        if fd not in self.open_files:
            return -1
        return self.open_files[fd].write(data)
