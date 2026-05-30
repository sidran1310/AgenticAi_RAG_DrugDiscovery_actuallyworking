import os
from typing import Iterable, List

import requests


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def download_structures(pdb_ids: Iterable[str], folder: str = None) -> List[str]:

    folder = folder or os.path.join(BASE_DIR, "pdb_files")

    if not os.path.exists(folder):
        os.makedirs(folder)

    downloaded_files = []

    for pdb_id in pdb_ids:

        pdb_id = str(pdb_id).strip().upper()
        if not pdb_id:
            continue

        pdb_url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
        cif_url = f"https://files.rcsb.org/download/{pdb_id}.cif"

        try:
            pdb_response = requests.get(pdb_url, timeout=15)
        except Exception:
            pdb_response = None

        if pdb_response is not None and pdb_response.status_code == 200 and pdb_response.text.strip():

            filepath = os.path.join(folder, pdb_id + ".pdb")

            with open(filepath, "w") as f:
                f.write(pdb_response.text)

            downloaded_files.append(filepath)

        else:

            try:
                cif_response = requests.get(cif_url, timeout=15)
            except Exception:
                cif_response = None

            if cif_response is not None and cif_response.status_code == 200 and cif_response.text.strip():

                filepath = os.path.join(folder, pdb_id + ".cif")

                with open(filepath, "w") as f:
                    f.write(cif_response.text)

                downloaded_files.append(filepath)

    return downloaded_files
