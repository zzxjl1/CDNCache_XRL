from faker import Faker
from utils import generate_version, GB2MB
import random

fake = Faker()


class Service():
    id_counter = 0

    def __init__(self,
                 name=None,
                 ) -> None:
        self.id = Service.id_counter
        Service.id_counter += 1
        self.name = name if name else fake.url()
        self.version = generate_version()
        self.size = random.randint(1*GB2MB, 100*GB2MB)

    def __str__(self) -> str:
        res = f"Service id: {self.id}\n"
        res += f"Name: {self.name}\n"
        res += f"Version: {self.version}\n"
        res += f"Size: {self.size} MB\n"
        return res


if __name__ == "__main__":
    s = Service()
    print(s)
