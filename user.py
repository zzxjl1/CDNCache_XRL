from faker import Faker
faker = Faker()


class User():
    def __init__(self):
        self.name = faker.name()
