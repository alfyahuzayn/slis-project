import frappe


@frappe.whitelist()
def get_labs():
    """
    Return laboratories based on user permissions.
    Administrator/System Manager -> All laboratories
    Other users -> Only permitted laboratories
    """

    user = frappe.session.user

    # Administrator / System Manager
    if user == "Administrator" or "System Manager" in frappe.get_roles(user):

        return frappe.get_all(
            "Soil Laboratory",
            fields=["name", "lab_name"],
            order_by="lab_name asc"
        )

    # User permitted laboratories
    allowed_labs = frappe.get_all(
        "User Permission",
        filters={
            "user": user,
            "allow": "Soil Laboratory"
        },
        pluck="for_value"
    )

    if not allowed_labs:
        return []

    return frappe.get_all(
        "Soil Laboratory",
        filters={
            "name": ["in", allowed_labs]
        },
        fields=["name", "lab_name"],
        order_by="lab_name asc"
    )


@frappe.whitelist()
def get_asset_category_chart(lab=None):
    """
    Return asset category count based on user permissions.
    """

    user = frappe.session.user

    conditions = []
    values = {}

    # ---------------------------------------------------
    # Administrator / System Manager
    # ---------------------------------------------------

    if user == "Administrator" or "System Manager" in frappe.get_roles(user):

        if lab:
            conditions.append("location=%(lab)s")
            values["lab"] = lab

    # ---------------------------------------------------
    # Normal Users
    # ---------------------------------------------------

    else:

        allowed_labs = frappe.get_all(
            "User Permission",
            filters={
                "user": user,
                "allow": "Soil Laboratory"
            },
            pluck="for_value"
        )

        if not allowed_labs:
            return {
                "labels": [],
                "values": []
            }

        conditions.append("location IN %(labs)s")
        values["labs"] = tuple(allowed_labs)

        if lab:
            conditions.append("location=%(lab)s")
            values["lab"] = lab

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    data = frappe.db.sql(f"""
        SELECT
            asset_category,
            COUNT(name) AS total
        FROM `tabAsset`
        {where_clause}
        GROUP BY asset_category
        ORDER BY asset_category
    """, values, as_dict=True)

    return {
        "labels": [d.asset_category for d in data],
        "values": [d.total for d in data]
    }