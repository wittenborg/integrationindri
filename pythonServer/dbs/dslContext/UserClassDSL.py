

class UserDSL:
    def __init__(self, con, cur):
        self.con = con
        self.cur = cur

    def create_user_table(self):
        return