# tasks.py
from celery import shared_task
from .models import BarCodePUN
from .forms import BatchBarcodeScanForm
from barcode.views import verify_barcode


@shared_task
def process_barcodes_task(current_part_id, barcodes):
    processed_barcodes = []
    current_part_PUN = BarCodePUN.objects.get(id=current_part_id)

    for barcode in barcodes:
        processed_barcodes.append(verify_barcode(current_part_id, barcode))

    # Return the processed barcodes
    return processed_barcodes
