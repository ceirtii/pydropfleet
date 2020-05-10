
class Weapon:

    gunDB = dict()

    def __init__(self):
        pass

    @staticmethod
    def load_gunDB():
        gunfile = open('guns.csv', encoding="utf-8-sig")
        gunreader = csv.reader(gunfile)