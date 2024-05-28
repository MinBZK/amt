class SystemCardService:
    def __init__(self):
        self.system_card = {}

    def update(self, title):
        self.system_card["title"] = title
        return self.system_card

    def get_system_card(self):
        return self.system_card
