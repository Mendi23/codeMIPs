# pycparser: using_cpp_libc.py
from _ast import AST

from pycparser import parse_file

from utils.file_paths import EXAMPLE_PATH

def parse_util() -> AST:
    return parse_file(EXAMPLE_PATH, use_cpp=True,
    cpp_path=r'C:\TDM-GCC-64\bin\gcc.exe',
    cpp_args=['-E', r'-Iutils/fake_libc_include'])


ast = parse_util()
ast.show()