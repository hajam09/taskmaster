from django.core.management.base import BaseCommand

from taskmaster.operations import seedDataOperations


class Command(BaseCommand):
    help = 'Seed data installer'

    def handle(self, *args, **kwargs):
        xmlFiles = seedDataOperations.getSeedDataFiles()

        self.stdout.write("Installing seed-data")
        for xmlFile in xmlFiles:
            self.stdout.write(f'File {xmlFile} is being processed')
            seedDataOperations.installSeedData(xmlFile)

        self.stdout.write("Seed data installed successfully")