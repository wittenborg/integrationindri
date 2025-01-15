
def find_table_name(table_name, tables):
    for table in tables:
        if table_name == table[0]:
            return True
    return False