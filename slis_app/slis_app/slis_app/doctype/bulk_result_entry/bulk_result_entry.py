import frappe
import json
from frappe.model.document import Document


class BulkResultEntry(Document):
    def on_update(self):

        # Build sample_id -> values_json lookup
        bulk_by_sample_id = {}

        for bulk_row in self.sample_data or []:
            if not bulk_row.sample_id:
                continue

            bulk_by_sample_id[bulk_row.sample_id] = bulk_row.values_json

        if not bulk_by_sample_id:
            return

        # Find Sample Data rows having the same sample_id
        # and belonging to Soil Test Result
        matching_rows = frappe.get_all(
            "Sample Data",
            filters={
                "sample_id": ["in", list(bulk_by_sample_id.keys())],
                "parenttype": "Soil Test Result",
                "parentfield": "test_sample_data"
            },
            fields=[
                "parent",
                "sample_id"
            ]
        )

        if not matching_rows:
            return

        # Get unique Soil Test Result documents
        parent_names = list(
            set(row.parent for row in matching_rows if row.parent)
        )

        for parent_name in parent_names:

            soil_test_result = frappe.get_doc(
                "Soil Test Result",
                parent_name
            )

            updated = False

            for test_row in soil_test_result.test_sample_data or []:

                if not test_row.sample_id:
                    continue

                if test_row.sample_id not in bulk_by_sample_id:
                    continue

                raw_values = bulk_by_sample_id.get(
                    test_row.sample_id
                )

                new_json = build_values_json(
                    raw_values,
                    test_row.sample_id
                )

                if new_json is None:
                    continue

                # Update only when value changed
                if test_row.values_json != new_json:

                    test_row.values_json = new_json

                    updated = True

            if updated:

                soil_test_result.flags.ignore_permissions = True

                soil_test_result.save(
                    ignore_permissions=True
                )


def build_values_json(raw_values, sample_id):

    try:

        bulk_data = json.loads(
            raw_values or "{}"
        )

    except (TypeError, ValueError):

        frappe.log_error(
            message=(
                "Invalid JSON in Bulk Result Entry\n"
                f"Sample ID: {sample_id}\n"
                f"Value: {raw_values}"
            ),
            title="Bulk Result Entry Invalid JSON"
        )

        return None

    final_data = {}

    for test_name, test_value in bulk_data.items():



        if isinstance(test_value, dict):

            if "result" in test_value:

                final_data[test_name] = (
                    test_value["result"]
                )

            else:

                # Keep existing simple value if available
                # instead of creating a false zero value
                continue

        else:

            final_data[test_name] = test_value

    return json.dumps(final_data)