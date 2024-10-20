from tree.nodes import FileNode, DirectoryNode
from pathlib import Path
from parsers.code_parser import CodeFlowParser
import re
from typing import Callable,List

def gitignore_filter(gitignore_path: Path) -> Callable[[Path], bool]:
    """
    Parses a .gitignore file and returns a lambda function that can be used to filter files
    according to .gitignore.
    """
    patterns = []
    base_dir = gitignore_path.parent

    with gitignore_path.open('r') as f:
        for line in f:
            line = line.rstrip('\n')
            
            if (line.startswith('#')) or (not line or line.strip() == ''):
                # Skip empty lines and comments
                continue  

            is_negated = False
            if line.startswith('!'):
                # Remove '!' from the pattern
                is_negated = True
                line = line[1:]

            pattern = line.strip()
            regex = gitignore_pattern_to_regex(pattern)
            patterns.append((is_negated, re.compile(regex)))

    def filter_func(file_path: Path) -> bool:
        matched = False
        try:
            rel_path = file_path.relative_to(base_dir)
        except ValueError:
            # current file is outside of base directory
            return True  
        
        str_path = str(rel_path.as_posix())
        for is_negated, regex in patterns:
            if regex.match(str_path):
                matched = not is_negated
        
        # True if included, False if ignored
        return not matched  

    return filter_func

def gitignore_pattern_to_regex(pattern: str) -> str:
    """
    Converts a .gitignore pattern to a regular expression.
    """
    # Handle special characters and wildcards
    pattern = pattern.strip()
    if pattern == '':
        return ''
    abs_pattern = pattern.startswith('/')
    dir_only = pattern.endswith('/')
    pattern = pattern.strip('/')
    regex = ''
    i, n = 0, len(pattern)
    while i < n:
        c = pattern[i]
        if c == '*':
            if (i + 1) < n and pattern[i+1] == '*':
                i += 1
                regex += '.*'
            else:
                regex += '[^/]*'
        elif c == '?':
            regex += '[^/]'
        else:
            regex += re.escape(c)
        i += 1
    if dir_only:
        regex += '(?:/.*)?'
    if abs_pattern:
        regex = '^' + regex + '$'
    else:
        regex = '(^|.*/)' + regex + '$'
    return regex

class RepoParser:

    def __init__(self):
        self.code_parser = CodeFlowParser()
        self.gitignore_filters: List[Callable[[Path], bool]] = []

    def parse(self, path: str) -> FileNode | DirectoryNode | None:
        entrypoint = Path(path)

        if not entrypoint.exists():
            raise Exception(f"Path '{entrypoint.absolute()}' does not exist")
        
        try:
            if entrypoint.is_file():
                with open(entrypoint,'r') as f:
                    program_node,a,b = self.code_parser.parse(f.read())
                    return FileNode(
                        path=entrypoint,
                        program=program_node
                    )
            else:
                return self._parse_directory(entrypoint)
            
        except Exception as e:
                raise Exception(f"Failed to parse code in file '{entrypoint.absolute()}'. {e}")
        
    def _parse_directory(self, entrypoint: Path) -> DirectoryNode:
        parent_node = DirectoryNode(path=entrypoint)

        all_files = sorted(Path.iterdir(entrypoint), key=lambda p: 0 if p.is_file() else 1)

        # Parse gitignore files first
        for gitignore_path in [x for x in all_files if x.is_file() and x.name == '.gitignore']:
            self.gitignore_filters.append(gitignore_filter(gitignore_path))
        
        # Parse rest of the files / folders
        for child_path in [file_path for file_path in all_files if file_path.name != '.gitignore']:
            should_skip = False

            for filter_check in self.gitignore_filters:
                if not filter_check(child_path):
                    should_skip = True
                    break

            if should_skip:
                continue

            if child_path.is_dir():
                parent_node.add_child(self._parse_directory(child_path))
            else:
                parent_node.add_child(self.parse(child_path))
        
        return parent_node

 
