CHUNK_SIZE = 2048  # 1 MB

def split_chunks(filepath):
    with open(filepath, 'rb') as f:
        while chunk := f.read(CHUNK_SIZE):
            yield chunk
