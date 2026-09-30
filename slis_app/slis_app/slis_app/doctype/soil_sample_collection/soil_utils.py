import re
import frappe

def set_master_reference_sample_id(doc):
    """
    Sets reference_sample_id for Master samples.
    """
    if not getattr(doc, "is_master_sample", False) or getattr(doc, "is_generated_sample", False):
        return

    num_samples = getattr(doc, "number_of_samples", None) or (len(doc.sample_data) if getattr(doc, "sample_data", None) else 1)

    # ---------------------------------------------------------
    # 1. FARMER & CONSULTANCY MASTER (BATCH FORMATTING)
    # ---------------------------------------------------------
    if doc.client_type in ["Farmer", "Consultancy"]:
        if num_samples > 1 and doc.name:
            doc.reference_sample_id = f"{doc.name}(1-{num_samples})"
        elif getattr(doc, "reference_name", None):
            doc.reference_sample_id = doc.name
        return

    # ---------------------------------------------------------
    # 2. DEPARTMENT SEQUENCE PARSING LOGIC
    # ---------------------------------------------------------
    if not getattr(doc, "sample_data", None) or len(doc.sample_data) == 0:
        return

    seq_numbers = []
    base_prefix = None

    for row in doc.sample_data:
        code_val = getattr(row, "sample_id", None) or getattr(row, "lab_code", None) or getattr(row, "reference_name", None)
        if not code_val:
            continue
            
        clean_id = str(code_val).strip().split(" ")[0]
        match = re.search(r'^(.*?/?)(\d+)$', clean_id)
        if match:
            prefix, seq_num = match.groups()
            if not base_prefix:
                base_prefix = prefix
            seq_numbers.append(int(seq_num))

    if not base_prefix or not seq_numbers:
        if getattr(doc, "reference_name", None):
            doc.reference_sample_id = doc.reference_name
        return

    start_seq = min(seq_numbers)
    end_seq = max(seq_numbers)
    clean_prefix = base_prefix.rstrip("/")

    if start_seq == end_seq:
        doc.reference_sample_id = f"{clean_prefix}/{start_seq}"
    else:
        doc.reference_sample_id = f"{clean_prefix}/({start_seq}-{end_seq})"