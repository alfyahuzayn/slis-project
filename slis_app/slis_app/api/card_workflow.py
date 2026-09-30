import frappe

@frappe.whitelist()
def get_workflow_counts():
    # Define mapping
    role_map = {
        "Soil Intaker L1": ["Draft", "Enter File number", "Returned to Senior Chemist(Overload)"],
        "Soil Intaker L2": ["With Assistant Director", "With PSC Officer", "Returned to Senior Chemist(Overload)"],
        "PSC Officer": ["With PSC Officer", "Returned to PSC (Overload)"],
        "Senior Chemist": ["With Senior Chemist"]
    }
    
    user_roles = frappe.get_roles()
    relevant_states = []
    
    for role, states in role_map.items():
        if role in user_roles:
            relevant_states.extend(states)
            
    relevant_states = list(set(relevant_states))
    
    if not relevant_states:
        return 0
        
    # Ensure all brackets are closed here
    return frappe.db.count("Soil Sample Collection", filters={
        "status": ["in", relevant_states],
        "docstatus": ["<", 2]
    })