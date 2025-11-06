# Text Merge and Split; Copyright (c) 2025 Idan Miara; Licensed under the MIT license.
import hashlib
from pathlib import Path
from sys import argv
from typing import Iterable

PathLike = str | Path
FilesMap = dict[PathLike, PathLike]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def merge(sentinel: str,
          inputs: FilesMap,
          output_path: Path | str,
          delimiter=':', encoding='utf-8'):
    """
    inputs maps a target filename to a source filename
    """
    with Path(output_path).open('wb') as out:
        for dst_name, input_filename in inputs.items():
            input_filename = Path(input_filename)
            if not input_filename.is_file():
                continue
            data = Path(input_filename).read_bytes()
            checksum = sha256(data)
            header = f"{dst_name}{delimiter}{len(data)}{delimiter}{checksum}"
            print(header)
            header = f"{sentinel}{delimiter}{header}\n"
            out.write(header.encode(encoding))
            out.write(data)
    print('Merge completed!')


def split(sentinel: str, merged_file: Path | str, output_path: Path | str, delimiter=':', encoding='utf-8') -> FilesMap:
    output_path = Path(output_path)
    merged_file = Path(merged_file)
    content = merged_file.read_bytes()
    sentinel = sentinel + delimiter
    parts = content.split(sentinel.encode(encoding))
    d = {}
    for part in parts[1:]:
        header, body = part.split(b"\n", 1)
        try:
            filename, size_str, checksum = header.decode().rsplit(delimiter, 2)
        except ValueError:
            raise ValueError(f"Invalid header: {header!r}")

        size = int(size_str)
        file_content = body[:size]
        actual_checksum = sha256(file_content)

        if actual_checksum != checksum:
            raise ValueError(f"Checksum mismatch for {filename}: expected {checksum}, got {actual_checksum}")

        filename = filename.strip()
        output_filename = output_path / filename
        output_filename.parent.mkdir(exist_ok=True, parents=True)
        output_filename.write_bytes(file_content)
        d[filename] = output_filename
    print('Split completed!')
    return d


def files_relative_to(files: Iterable[PathLike], relative_to: PathLike | None = None) -> FilesMap:
    """
    if relative_to is None: keys are filenames
    elif relative_to is an empty string: keys are full path
    else keys are relative to relative_to
    """
    files = [Path(f) for f in files]
    if relative_to is None:
        return {f.name: f for f in files}
    elif relative_to == '':
        return {f: f for f in files}
    else:
        return {f.relative_to(relative_to): f for f in files}


def add_dir(input_dir: PathLike, input_pattern: str) -> Iterable[PathLike]:
    input_dir = Path(input_dir)
    if input_dir.is_dir():
        return [f for f in sorted(input_dir.glob(str(input_pattern))) if f.is_file()]
    else:
        raise Exception(f"{input_dir} is not a dir")


def assert_files_exist(files: Iterable[PathLike]):
    for f in files:
        if not Path(f).is_file():
            raise Exception(f"Input {f} not found!")


def main(input_path: PathLike):
    sentinel = "--STARTFILE--"
    input_path = str(input_path)
    output_path = input_path + '.out'
    if Path(input_path).is_dir():
        merged_file = input_path + '.txt'
        input_pattern = "**/*"
        include_merger = True
        inputs = files_relative_to(
            add_dir(input_dir=input_path, input_pattern=input_pattern),
            relative_to=input_path)
        if include_merger:
            inputs = files_relative_to([__file__], relative_to=None) | inputs
        assert_files_exist(inputs.values())
        merge(sentinel=sentinel, inputs=inputs, output_path=merged_file)
    else:
        merged_file = input_path
    split(sentinel=sentinel, merged_file=merged_file, output_path=output_path)


if __name__ == '__main__':
    for name in argv[1:]:
        main(name)
        # main(name+'.txt')
