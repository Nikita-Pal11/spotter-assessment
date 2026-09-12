import csv
from django.core.management.base import BaseCommand
from core.models import FuelStop

class Command(BaseCommand):
    help = "Import fuel prices from CSV"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)

    def handle(self, *args, **options):
        path = options["csv_path"]
        created_count = 0

        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            stations = []
            for row in reader:
                stations.append(FuelStop(
                    truckstop_id=int(row["OPIS Truckstop ID"]),
                    name=row["Truckstop Name"].strip(),
                    address=row["Address"].strip(),
                    city=row["City"].strip(),
                    state=row["State"].strip(),
                    rack_id=int(row["Rack ID"]),
                    price=float(row["Retail Price"]),
                ))

            FuelStop.objects.bulk_create(stations, batch_size=1000)
            created_count = len(stations)

        self.stdout.write(self.style.SUCCESS(f"Imported {created_count} stations"))