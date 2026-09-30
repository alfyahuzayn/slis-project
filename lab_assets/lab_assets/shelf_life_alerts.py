
import frappe
from frappe.utils import getdate, today, date_diff


def check_shelf_life_alerts():
    """
    Check batches with available stock and create shelf-life
    notifications for users permitted for the respective lab.
    """

    today_date = getdate(today())

    # Get all batches which have an expiry date
    batches = frappe.db.sql(
        """
        SELECT
            b.name AS batch_no,
            b.item AS item_code,
            b.expiry_date,
            i.item_name,
            i.custom_shelf_life_alert_before_days
        FROM `tabBatch` b
        INNER JOIN `tabItem` i
            ON i.name = b.item
        WHERE
            b.expiry_date IS NOT NULL
            AND i.has_batch_no = 1
            AND i.has_expiry_date = 1
            AND i.custom_shelf_life_alert_before_days IS NOT NULL
            AND i.custom_shelf_life_alert_before_days != ''
        """,
        as_dict=True,
    )

    for batch in batches:

        # Convert Data field to integer
        try:
            alert_before_days = int(
                batch.custom_shelf_life_alert_before_days
            )
        except (ValueError, TypeError):
            continue

        if alert_before_days <= 0:
            continue

        # Calculate remaining shelf-life days
        days_remaining = date_diff(
            getdate(batch.expiry_date),
            today_date
        )

        # Get current quantity of this batch in each lab
        stock_list = get_batch_stock(batch.batch_no)

        for stock in stock_list:

            warehouse = stock.warehouse
            qty = float(stock.qty or 0)

            # Don't alert if there is no current stock
            if qty <= 0:
                continue

            # ------------------------------------------------
            # EXPIRED
            # ------------------------------------------------
            if days_remaining < 0:

                send_batch_notification(
                    batch=batch,
                    warehouse=warehouse,
                    qty=qty,
                    days_remaining=days_remaining,
                    alert_type="Expired"
                )

            # ------------------------------------------------
            # EXPIRING SOON
            # ------------------------------------------------
            elif days_remaining <= alert_before_days:

                send_batch_notification(
                    batch=batch,
                    warehouse=warehouse,
                    qty=qty,
                    days_remaining=days_remaining,
                    alert_type="Expiring Soon"
                )


def get_batch_stock(batch_no):
    """
    Get current quantity of a batch in each warehouse/lab.

    ERPNext v15 uses Serial and Batch Bundle, so the
    batch information is obtained from Serial and Batch Entry.
    """

    return frappe.db.sql(
        """
        SELECT
            sbe.warehouse,

            SUM(
                CASE
                    WHEN sbe.is_outward = 1
                        THEN -ABS(sbe.qty)
                    ELSE ABS(sbe.qty)
                END
            ) AS qty

        FROM `tabSerial and Batch Entry` sbe

        INNER JOIN `tabSerial and Batch Bundle` sab
            ON sab.name = sbe.parent

        WHERE
            sbe.batch_no = %(batch_no)s
            AND sab.docstatus = 1
            AND sab.is_cancelled = 0
            AND sab.is_rejected = 0

        GROUP BY
            sbe.warehouse

        HAVING
            qty > 0
        """,
        {
            "batch_no": batch_no
        },
        as_dict=True,
    )


def get_lab_users(warehouse):
    """
    Get enabled users who have User Permission
    for the particular Warehouse/Lab.
    """

    return frappe.db.sql(
        """
        SELECT DISTINCT
            up.user

        FROM `tabUser Permission` up

        INNER JOIN `tabUser` u
            ON u.name = up.user

        WHERE
            up.allow = 'Warehouse'
            AND up.for_value = %(warehouse)s
            AND u.enabled = 1
        """,
        {
            "warehouse": warehouse
        },
        pluck="user",
    )


def send_batch_notification(
    batch,
    warehouse,
    qty,
    days_remaining,
    alert_type
):
    """
    Send notification to the users belonging to the lab.
    """

    users = get_lab_users(warehouse)

    if not users:
        return

    # ------------------------------------------------
    # Notification content
    # ------------------------------------------------

    if alert_type == "Expired":

        subject = f"Expired Stock Alert: {batch.item_name}"

        message = f"""
        <b>Expired Stock Alert</b><br><br>

        <b>Item:</b> {batch.item_name}<br>
        <b>Batch:</b> {batch.batch_no}<br>
        <b>Laboratory:</b> {warehouse}<br>
        <b>Quantity:</b> {qty}<br>
        <b>Expiry Date:</b> {batch.expiry_date}<br>
        <b>Status:</b> Expired
        """

    else:

        subject = f"Shelf Life Alert: {batch.item_name}"

        message = f"""
        <b>Shelf Life Alert</b><br><br>

        <b>Item:</b> {batch.item_name}<br>
        <b>Batch:</b> {batch.batch_no}<br>
        <b>Laboratory:</b> {warehouse}<br>
        <b>Quantity:</b> {qty}<br>
        <b>Expiry Date:</b> {batch.expiry_date}<br>
        <b>Days Remaining:</b> {days_remaining}<br>
        <b>Status:</b> Expiring Soon
        """

    # ------------------------------------------------
    # Send to each permitted user
    # ------------------------------------------------

    for user in users:

        if notification_already_sent(
            user=user,
            batch_no=batch.batch_no,
            alert_type=alert_type
        ):
            continue

        create_notification(
            user=user,
            subject=subject,
            message=message,
            batch_no=batch.batch_no,
            item_code=batch.item_code
        )


def notification_already_sent(
    user,
    batch_no,
    alert_type
):
    """
    Prevent duplicate notifications.

    The notification is displayed against the Item,
    but duplicate checking is still performed against
    the specific Batch.
    """

    if alert_type == "Expired":
        subject = "Expired Stock Alert:"
    else:
        subject = "Shelf Life Alert:"

    return frappe.db.exists(
        "Notification Log",
        {
            "for_user": user,
            "type": "Alert",
            "subject": ["like", f"{subject}%"],
            "email_content": ["like", f"%<b>Batch:</b> {batch_no}%"],
        }
    )


def create_notification(
    user,
    subject,
    message,
    batch_no,
    item_code
):
    """
    Create Frappe System Notification.

    Notification is linked to the Item instead of Batch,
    so users do not need Batch permission.
    """

    frappe.get_doc(
        {
            "doctype": "Notification Log",
            "for_user": user,
            "type": "Alert",
            "subject": subject,
            "email_content": message,

            # Link notification to Item instead of Batch
            "document_type": "Item",
            "document_name": item_code,

            "read": 0,
            "from_user": "Administrator",

            # User can open Item directly
            "link": f"/app/item/{item_code}",
        }
    ).insert(ignore_permissions=True)

    frappe.db.commit()