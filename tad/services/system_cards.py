# TODO: change name ... (make that it has a clear relation with https://github.com/MinBZK/ai-validation/blob/main/docs/projects/tad/reporting-standard/latest.md)
class SystemCards:
    def __init__(self):
        pass

    def create(self):
        pass

    def update(self, context):
        # TODO: make a task in TAD based on the instrument register (OUT OF SCOPE FOR THIS TICKET)
        # TODO: Assume systemcard already exists of the project and this will add model/assesssments cards (ASSUMPTION)
        # TODO: What if a systemcard does not exist yet? It this a task in TAD as well? (EXTRA CASE)
        # TODO: input format research (https://github.com/MinBZK/instrument-registry/tree/add-iama-tasks) (ASSUMPTION)

        # Functionality from instrument to TAD datamodel
        # TODO: hoe koppelen we het instrument aan de taak?

        # functionality of writing systemcard away
        # TODO: Upload to where? Do we have a button in the UI to download it (ASSUMPTION SCENARIO 1)
        # TODO: Pushing the system card to a git repository via SSH? User needs to provide the SSH & repo somewhere (ASSUMPTION SCENARIO 2)
        # TODO: Every time a task is moved to done, we will write it away locally, step up to SCENARIO 2(ASSUMPTION SCENARIO 1.5)
        pass
