import os


def split_into_chunks(items, chunk_size):
    if chunk_size <= 0:
        raise ValueError('Размер чанка должен быть больше 0')
    return [items[index:index + chunk_size] for index in range(0, len(items), chunk_size)]


def get_chronicle_base_dir(output_root_dir, start_date_str, end_date_str):
    return os.path.join(output_root_dir, f'chronicle-{start_date_str}_{end_date_str}')