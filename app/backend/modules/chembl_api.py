import requests
from typing import List, Dict, Any, Optional

CHEMBL_BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"

def search_chembl(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Searches the ChEMBL database for molecules with detailed information.
    """
    query = (query or "").strip()
    if not query:
        return []

    try:
        # First, search for molecules by name/synonym
        molecule_url = f"{CHEMBL_BASE_URL}/molecule.json"
        molecule_params = {
            "molecule_synonyms__molecule_synonym__icontains": query,
            "limit": limit,
            "only": "molecule_chembl_id,pref_name,molecule_type,max_phase,molecule_properties,indication_class"
        }

        molecule_response = requests.get(molecule_url, params=molecule_params, timeout=15)
        molecule_response.raise_for_status()
        molecule_data = molecule_response.json()

        results = []
        molecules = molecule_data.get("molecules", [])

        for mol in molecules:
            chembl_id = mol.get("molecule_chembl_id")
            if not chembl_id:
                continue

            # Get detailed molecule information
            detail_url = f"{CHEMBL_BASE_URL}/molecule/{chembl_id}.json"
            try:
                detail_response = requests.get(detail_url, timeout=10)
                detail_response.raise_for_status()
                detail_data = detail_response.json()

                molecule = detail_data.get("molecule", {})

                # Extract properties
                properties = molecule.get("molecule_properties", {}) or {}
                structures = molecule.get("molecule_structures", {}) or {}

                result = {
                    "chembl_id": chembl_id,
                    "name": molecule.get("pref_name", "Unknown Name"),
                    "synonyms": [syn.get("molecule_synonym") for syn in molecule.get("molecule_synonyms", []) if syn.get("molecule_synonym")][:5],
                    "type": molecule.get("molecule_type", "Unknown Type"),
                    "max_phase": molecule.get("max_phase", 0),
                    "indication_class": molecule.get("indication_class"),
                    "therapeutic_flag": molecule.get("therapeutic_flag", False),
                    "dosed_ingredient": molecule.get("dosed_ingredient", False),
                    "oral": molecule.get("oral", False),
                    "parenteral": molecule.get("parenteral", False),
                    "topical": molecule.get("topical", False),
                    "black_box_warning": molecule.get("black_box_warning", False),
                    "natural_product": molecule.get("natural_product", False),
                    "first_approval": molecule.get("first_approval"),
                    "oral": molecule.get("oral", False),
                    "availability_type": molecule.get("availability_type"),
                    "withdrawn_flag": molecule.get("withdrawn_flag", False),
                    "withdrawn_year": molecule.get("withdrawn_year"),
                    "withdrawn_country": molecule.get("withdrawn_country"),
                    "withdrawn_reason": molecule.get("withdrawn_reason"),
                    # Properties
                    "molecular_weight": properties.get("mw_freebase"),
                    "alogp": properties.get("alogp"),
                    "hbd": properties.get("hbd"),
                    "hba": properties.get("hba"),
                    "psa": properties.get("psa"),
                    "rtb": properties.get("rtb"),
                    "ro3_pass": properties.get("ro3_pass"),
                    "num_ro5_violations": properties.get("num_ro5_violations"),
                    "cx_logp": properties.get("cx_logp"),
                    "cx_logd": properties.get("cx_logd"),
                    "aromatic_rings": properties.get("aromatic_rings"),
                    "heavy_atoms": properties.get("heavy_atoms"),
                    "qed_weighted": properties.get("qed_weighted"),
                    # Structures
                    "smiles": structures.get("canonical_smiles"),
                    "inchi": structures.get("standard_inchi"),
                    "inchikey": structures.get("standard_inchi_key"),
                    # Source
                    "source": "ChEMBL"
                }

                results.append(result)

            except Exception as e:
                print(f"[ChEMBL] Failed to get details for {chembl_id}: {e}")
                # Add basic info if detailed fetch fails
                results.append({
                    "chembl_id": chembl_id,
                    "name": mol.get("pref_name", "Unknown Name"),
                    "type": mol.get("molecule_type", "Unknown Type"),
                    "max_phase": mol.get("max_phase", 0),
                    "source": "ChEMBL"
                })

        return results

    except Exception as e:
        print(f"[ChEMBL API] Error: {str(e)}")
        return []

def search_chembl_targets(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search for targets associated with a compound or disease.
    """
    try:
        # Search for activities first
        activity_url = f"{CHEMBL_BASE_URL}/activity.json"
        activity_params = {
            "molecule_chembl_id__icontains": query,
            "limit": limit,
            "only": "target_chembl_id,molecule_chembl_id,standard_type,standard_value,standard_units"
        }

        activity_response = requests.get(activity_url, params=activity_params, timeout=15)
        activity_response.raise_for_status()
        activity_data = activity_response.json()

        targets = {}
        activities = activity_data.get("activities", [])

        for activity in activities:
            target_id = activity.get("target_chembl_id")
            if target_id and target_id not in targets:
                targets[target_id] = {
                    "target_chembl_id": target_id,
                    "activities": []
                }
            if target_id:
                targets[target_id]["activities"].append({
                    "molecule_chembl_id": activity.get("molecule_chembl_id"),
                    "assay_type": activity.get("standard_type"),
                    "value": activity.get("standard_value"),
                    "units": activity.get("standard_units")
                })

        # Get target details
        results = []
        for target_id, data in targets.items():
            try:
                target_url = f"{CHEMBL_BASE_URL}/target/{target_id}.json"
                target_response = requests.get(target_url, timeout=10)
                target_response.raise_for_status()
                target_data = target_response.json()

                target_info = target_data.get("target", {})
                results.append({
                    "target_chembl_id": target_id,
                    "target_name": target_info.get("pref_name"),
                    "target_type": target_info.get("target_type"),
                    "organism": target_info.get("organism"),
                    "activities": data["activities"][:10],  # Limit activities
                    "source": "ChEMBL"
                })

            except Exception as e:
                print(f"[ChEMBL] Failed to get target details for {target_id}: {e}")

        return results

    except Exception as e:
        print(f"[ChEMBL API] Target search error: {str(e)}")
        return []

def get_chembl_assays(chembl_id: str) -> List[Dict[str, Any]]:
    """
    Get assay information for a specific compound.
    """
    try:
        assay_url = f"{CHEMBL_BASE_URL}/assay.json"
        assay_params = {
            "molecule_chembl_id": chembl_id,
            "limit": 50
        }

        assay_response = requests.get(assay_url, params=assay_params, timeout=15)
        assay_response.raise_for_status()
        assay_data = assay_response.json()

        assays = []
        for assay in assay_data.get("assays", []):
            assays.append({
                "assay_chembl_id": assay.get("assay_chembl_id"),
                "assay_type": assay.get("assay_type"),
                "assay_organism": assay.get("assay_organism"),
                "assay_description": assay.get("description"),
                "confidence_score": assay.get("confidence_score"),
                "source": "ChEMBL"
            })

        return assays

    except Exception as e:
        print(f"[ChEMBL API] Assay search error for {chembl_id}: {str(e)}")
        return []