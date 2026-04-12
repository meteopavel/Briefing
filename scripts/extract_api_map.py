"""
Собирает карту Python API по файлу или директории и сохраняет её в markdown рядом со скриптом.
Использование:
    python scripts/extract_api_map.py app/services/chronicle/prompts.py
    python scripts/extract_api_map.py app/services
    python scripts/extract_api_map.py app
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def has_dataclass_decorator(node: ast.ClassDef) -> bool:
    """Проверяет, помечен ли класс декоратором @dataclass."""
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == 'dataclass':
            return True
        if isinstance(decorator, ast.Attribute) and decorator.attr == 'dataclass':
            return True
        if isinstance(decorator, ast.Call):
            func = decorator.func
            if isinstance(func, ast.Name) and func.id == 'dataclass':
                return True
            if isinstance(func, ast.Attribute) and func.attr == 'dataclass':
                return True
    return False


def get_function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Собирает строковое представление сигнатуры функции из AST-узла."""
    args = []
    positional_args = node.args.args
    defaults = node.args.defaults
    defaults_offset = len(positional_args) - len(defaults)
    for index, arg in enumerate(positional_args):
        arg_text = arg.arg
        if arg.annotation is not None:
            arg_text += f': {ast.unparse(arg.annotation)}'
        if index >= defaults_offset:
            default_value = defaults[index - defaults_offset]
            arg_text += f' = {ast.unparse(default_value)}'
        args.append(arg_text)
    if node.args.vararg:
        vararg_text = f'*{node.args.vararg.arg}'
        if node.args.vararg.annotation is not None:
            vararg_text += f': {ast.unparse(node.args.vararg.annotation)}'
        args.append(vararg_text)
    for kwarg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
        kwarg_text = kwarg.arg
        if kwarg.annotation is not None:
            kwarg_text += f': {ast.unparse(kwarg.annotation)}'
        if default is not None:
            kwarg_text += f' = {ast.unparse(default)}'
        args.append(kwarg_text)
    if node.args.kwarg:
        kwarg_text = f'**{node.args.kwarg.arg}'
        if node.args.kwarg.annotation is not None:
            kwarg_text += f': {ast.unparse(node.args.kwarg.annotation)}'
        args.append(kwarg_text)
    signature = f'{node.name}({", ".join(args)})'
    if node.returns is not None:
        signature += f' -> {ast.unparse(node.returns)}'
    return signature


def get_class_signature(node: ast.ClassDef) -> str:
    """Собирает строковое представление объявления класса."""
    if has_dataclass_decorator(node):
        return f'{node.name} [dataclass]'
    return node.name


def get_class_fields(node: ast.ClassDef) -> list[str]:
    """Извлекает поля класса из аннотированных присваиваний на верхнем уровне тела класса."""
    fields = []
    for item in node.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            field_text = item.target.id
            if item.annotation is not None:
                field_text += f': {ast.unparse(item.annotation)}'
            if item.value is not None:
                field_text += f' = {ast.unparse(item.value)}'
            fields.append(field_text)
    return fields


def get_class_methods(node: ast.ClassDef) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Возвращает методы класса верхнего уровня."""
    return [
        item
        for item in node.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def format_docstring(docstring: str | None, indent: str = '') -> list[str]:
    """Преобразует докстринг в список строк с нужным отступом."""
    if not docstring:
        return [f'{indent}Нет докстринга.']
    lines = docstring.strip().splitlines()
    return [f'{indent}{line.rstrip()}' for line in lines]


def is_meaningful_python_file(file_path: Path) -> bool:
    """
    Проверяет, содержит ли Python-файл значимую API-информацию для карты.
    Значимыми считаются:
    - модульный докстринг;
    - функции;
    - классы.
    Импорты, константы и пустые __init__.py сами по себе не считаются достаточными.
    """
    source = file_path.read_text(encoding='utf-8')
    tree = ast.parse(source)
    if ast.get_docstring(tree):
        return True
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return True
    return False


def extract_python_file_info(file_path: Path) -> str:
    """Извлекает модульный докстринг, классы, функции и их докстринги из Python-файла."""
    source = file_path.read_text(encoding='utf-8')
    tree = ast.parse(source)
    module_docstring = ast.get_docstring(tree)
    lines = [f'# {file_path.as_posix()}']
    if module_docstring:
        lines.append('')
        lines.append('Модуль:')
        lines.extend(format_docstring(module_docstring))
    classes = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    ]
    functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    if classes:
        lines.append('')
        lines.append('Классы:')
    for class_node in classes:
        signature = get_class_signature(class_node)
        docstring = ast.get_docstring(class_node)
        lines.append('')
        lines.append(f'- `{signature}`')
        lines.extend(format_docstring(docstring, indent='  '))
        fields = get_class_fields(class_node)
        if fields:
            lines.append('  Поля:')
            for field in fields:
                lines.append(f'  - `{field}`')
        methods = get_class_methods(class_node)
        if methods:
            lines.append('  Методы:')
            for method_node in methods:
                method_signature = get_function_signature(method_node)
                method_docstring = ast.get_docstring(method_node)
                lines.append(f'  - `{method_signature}`')
                lines.extend(format_docstring(method_docstring, indent='    '))
    if functions:
        lines.append('')
        lines.append('Функции:')
    for function_node in functions:
        signature = get_function_signature(function_node)
        docstring = ast.get_docstring(function_node)
        lines.append('')
        lines.append(f'- `{signature}`')
        lines.extend(format_docstring(docstring, indent='  '))
    return '\n'.join(lines)


def collect_python_files(target_path: Path) -> list[Path]:
    """Собирает список значимых Python-файлов из файла или директории."""
    if target_path.is_file():
        if target_path.suffix != '.py':
            raise ValueError(f'Ожидался Python-файл: {target_path}')
        return [target_path] if is_meaningful_python_file(target_path) else []
    if target_path.is_dir():
        return sorted(
            file_path
            for file_path in target_path.rglob('*.py')
            if file_path.is_file() and is_meaningful_python_file(file_path)
        )
    raise ValueError(f'Путь не найден: {target_path}')


def build_output_filename(target_path: Path) -> Path:
    """Строит имя выходного markdown-файла рядом со скриптом."""
    normalized_name = target_path.as_posix().strip('/').replace('/', '_').replace('.', '_')
    filename = f'api_map__{normalized_name}.md'
    return SCRIPT_DIR / filename


def build_report(target_path: Path, files: list[Path]) -> str:
    """Собирает общий markdown-отчёт по одному файлу или набору файлов."""
    lines = [
        f'# API map: {target_path.as_posix()}',
        '',
        f'Найдено Python-файлов: {len(files)}',
    ]
    for file_path in files:
        lines.append('')
        lines.append('---')
        lines.append('')
        lines.append(extract_python_file_info(file_path))
    return '\n'.join(lines)


def main() -> None:
    """Точка входа: собирает API map по файлу или директории и сохраняет её в markdown-файл."""
    if len(sys.argv) < 2:
        raise SystemExit(
            'Использование: python scripts/extract_api_map.py <path_to_python_file_or_directory>',
        )
    target_path = Path(sys.argv[1])
    if not target_path.exists():
        raise SystemExit(f'Путь не найден: {target_path}')
    files = collect_python_files(target_path)
    if not files:
        raise SystemExit(f'Не найдено подходящих Python-файлов для карты API: {target_path}')
    report = build_report(target_path, files)
    output_file = build_output_filename(target_path)
    output_file.write_text(report, encoding='utf-8')
    print(f'Готово: {output_file}')


if __name__ == '__main__':
    main()
