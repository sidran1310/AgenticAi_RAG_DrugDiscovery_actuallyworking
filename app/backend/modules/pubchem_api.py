from typing import Any, Dict, Optional, List
import requests

PUBCHEM_BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

def _lipinski_pass(props: Dict[str, Any]) -> bool:
    """Check if compound passes Lipinski's Rule of Five."""
    try:
        mw = float(props.get("MolecularWeight") or 0)
        logp = float(props.get("XLogP") or 0)
        hbd = int(props.get("HBondDonorCount") or 0)
        hba = int(props.get("HBondAcceptorCount") or 0)
        return mw <= 500 and logp <= 5 and hbd <= 5 and hba <= 10
    except (ValueError, TypeError):
        return False

def _veber_pass(props: Dict[str, Any]) -> bool:
    """Check if compound passes Veber rules."""
    try:
        tpsa = float(props.get("TPSA") or 0)
        rtb = int(props.get("RotatableBondCount") or 0)
        return tpsa <= 140 and rtb <= 10
    except (ValueError, TypeError):
        return False

def _ghose_pass(props: Dict[str, Any]) -> bool:
    """Check if compound passes Ghose filter."""
    try:
        mw = float(props.get("MolecularWeight") or 0)
        logp = float(props.get("XLogP") or 0)
        rtb = int(props.get("RotatableBondCount") or 0)
        return (160 <= mw <= 480 and -0.4 <= logp <= 5.6 and
                20 <= rtb <= 130 and 0.5 <= props.get("Refractivity", 0) <= 130)
    except (ValueError, TypeError):
        return False

def get_pubchem(compound: str) -> Optional[Dict[str, Any]]:
    """Fetch comprehensive compound properties from PubChem."""
    compound = (compound or "").strip()
    if not compound:
        return None

    try:
        # Get basic properties
        props_url = f"{PUBCHEM_BASE_URL}/compound/name/{compound}/property/" \
                   "MolecularFormula,MolecularWeight,XLogP,TPSA,HBondDonorCount," \
                   "HBondAcceptorCount,RotatableBondCount,ExactMass,MonoisotopicMass," \
                   "HeavyAtomCount,AtomStereoCount,BondStereoCount,Complexity," \
                   "Charge,IUPACName,CanonicalSMILES,IsomericSMILES,InChI,InChIKey," \
                   "CovalentUnitCount,FeatureCount3D,FeatureAcceptorCount3D," \
                   "FeatureDonorCount3D,FeatureAnionCount3D,FeatureCationCount3D," \
                   "FeatureRingCount3D,FeatureHydrophobeCount3D,ConformerCount3D," \
                   "Fingerprint2D/JSON"

        response = requests.get(props_url, timeout=15)
        response.raise_for_status()
        data = response.json()

        if "PropertyTable" not in data or not data["PropertyTable"]["Properties"]:
            return None

        props = data["PropertyTable"]["Properties"][0]

        # Get synonyms
        synonyms_url = f"{PUBCHEM_BASE_URL}/compound/name/{compound}/synonyms/JSON"
        synonyms_response = requests.get(synonyms_url, timeout=10)
        synonyms = []
        if synonyms_response.status_code == 200:
            synonyms_data = synonyms_response.json()
            if "InformationList" in synonyms_data:
                info = synonyms_data["InformationList"]["Information"][0]
                synonyms = info.get("Synonym", [])[:10]  # Limit to 10 synonyms

        # Get classification
        classification_url = f"{PUBCHEM_BASE_URL}/compound/name/{compound}/classification/JSON"
        classification = {}
        try:
            class_response = requests.get(classification_url, timeout=10)
            if class_response.status_code == 200:
                class_data = class_response.json()
                if "Hierarchies" in class_data and class_data["Hierarchies"]["Hierarchy"]:
                    hierarchy = class_data["Hierarchies"]["Hierarchy"][0]
                    classification = {
                        "kingdom": hierarchy.get("Kingdom"),
                        "superclass": hierarchy.get("Superclass"),
                        "class": hierarchy.get("Class"),
                        "subclass": hierarchy.get("Subclass")
                    }
        except:
            pass  # Classification is optional

        molecular_weight = float(props.get("MolecularWeight") or 0)
        logp = props.get("XLogP")
        logp_val = float(logp) if logp is not None else None

        return {
            "compound": compound,
            "name": compound,
            "cid": props.get("CID"),
            "iupac_name": props.get("IUPACName"),
            "synonyms": synonyms,
            "formula": props.get("MolecularFormula"),
            "weight": molecular_weight,
            "molecular_weight": molecular_weight,
            "exact_mass": float(props.get("ExactMass") or 0),
            "monoisotopic_mass": float(props.get("MonoisotopicMass") or 0),
            "smiles": props.get("CanonicalSMILES"),
            "isomeric_smiles": props.get("IsomericSMILES"),
            "inchi": props.get("InChI"),
            "inchikey": props.get("InChIKey"),
            "logp": logp_val,
            "tpsa": float(props.get("TPSA") or 0),
            "hbd": int(props.get("HBondDonorCount") or 0),
            "hba": int(props.get("HBondAcceptorCount") or 0),
            "rotatable_bonds": int(props.get("RotatableBondCount") or 0),
            "heavy_atoms": int(props.get("HeavyAtomCount") or 0),
            "atom_stereo_count": int(props.get("AtomStereoCount") or 0),
            "bond_stereo_count": int(props.get("BondStereoCount") or 0),
            "complexity": float(props.get("Complexity") or 0),
            "charge": int(props.get("Charge") or 0),
            "covalent_units": int(props.get("CovalentUnitCount") or 0),
            "conformer_count": int(props.get("ConformerCount3D") or 0),
            "lipinski_pass": _lipinski_pass(props),
            "veber_pass": _veber_pass(props),
            "ghose_pass": _ghose_pass(props),
            "classification": classification,
            "fingerprint": props.get("Fingerprint2D"),
            "source": "PubChem",
            "url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{props.get('CID')}" if props.get("CID") else None
        }
    except Exception as exc:
        print(f"[PubChem] Lookup failed for {compound!r}: {exc}")
        return None

def search_pubchem_similar(smiles: str, threshold: float = 0.8, limit: int = 10) -> List[Dict[str, Any]]:
    """Find compounds similar to the given SMILES string."""
    if not smiles:
        return []

    try:
        similarity_url = f"{PUBCHEM_BASE_URL}/compound/similarity/smiles/{smiles}/JSON"
        params = {
            "Threshold": int(threshold * 100),  # Convert to percentage
            "MaxRecords": limit
        }

        response = requests.get(similarity_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        results = []
        if "PC_Compounds" in data:
            for compound in data["PC_Compounds"][:limit]:
                # Extract basic info from compound data
                props = compound.get("props", [])
                cid = compound.get("id", {}).get("id", {}).get("cid")

                # Find molecular formula and weight
                formula = None
                weight = None
                for prop in props:
                    if prop.get("urn", {}).get("label") == "Molecular Formula":
                        formula = prop.get("value", {}).get("sval")
                    elif prop.get("urn", {}).get("label") == "Molecular Weight":
                        weight = float(prop.get("value", {}).get("sval") or 0)

                results.append({
                    "cid": cid,
                    "formula": formula,
                    "molecular_weight": weight,
                    "source": "PubChem",
                    "url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}" if cid else None
                })

        return results

    except Exception as e:
        print(f"[PubChem] Similarity search failed for {smiles}: {e}")
        return []

def get_pubchem_by_cid(cid: int) -> Optional[Dict[str, Any]]:
    """Get compound information by PubChem CID."""
    try:
        props_url = f"{PUBCHEM_BASE_URL}/compound/cid/{cid}/property/" \
                   "MolecularFormula,MolecularWeight,XLogP,TPSA,HBondDonorCount," \
                   "HBondAcceptorCount,RotatableBondCount,CanonicalSMILES,IUPACName/JSON"

        response = requests.get(props_url, timeout=12)
        response.raise_for_status()
        data = response.json()

        if "PropertyTable" not in data or not data["PropertyTable"]["Properties"]:
            return None

        props = data["PropertyTable"]["Properties"][0]

        return {
            "cid": cid,
            "name": props.get("IUPACName", f"Compound {cid}"),
            "formula": props.get("MolecularFormula"),
            "molecular_weight": float(props.get("MolecularWeight") or 0),
            "smiles": props.get("CanonicalSMILES"),
            "logp": float(props.get("XLogP") or 0),
            "tpsa": float(props.get("TPSA") or 0),
            "hbd": int(props.get("HBondDonorCount") or 0),
            "hba": int(props.get("HBondAcceptorCount") or 0),
            "rotatable_bonds": int(props.get("RotatableBondCount") or 0),
            "lipinski_pass": _lipinski_pass(props),
            "source": "PubChem",
            "url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
        }

    except Exception as e:
        print(f"[PubChem] CID lookup failed for {cid}: {e}")
        return None
